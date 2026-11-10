"""Reconciliation: check every metric against an independent hand-written query.

For each check below, this script
  1. asks MetricFlow for the metric (`mf query ... --csv`), and
  2. runs the matching SQL file in reconciliation/ directly against the
     warehouse,
then compares the two result sets row by row. Any missing row or differing
value fails the run (exit code 1), so CI goes red.

Run after `dbt build`:
    python scripts/reconcile.py
"""
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "reconciliation"
DATABASE = ROOT / "subscription_metrics.duckdb"
TOLERANCE = 1e-9

# (metric, MetricFlow group-by, hand-written SQL file)
CHECKS = [
    ("new_subscriptions", "metric_time__month", "new_subscriptions_by_month.sql"),
    ("cancellations", "metric_time__month", "cancellations_by_month.sql"),
    ("net_new_subscriptions", "metric_time__month", "net_new_subscriptions_by_month.sql"),
    ("active_subscriptions", "metric_time__month", "active_subscriptions_by_month.sql"),
    ("retention_rate_90d", "subscription__plan", "retention_rate_90d_by_plan.sql"),
]


def normalize_key(value) -> str:
    """Make dates and labels comparable: '2026-01-01 00:00:00' -> '2026-01-01'."""
    return str(value)[:10]


def query_metricflow(metric: str, group_by: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "result.csv"
        subprocess.run(
            ["mf", "query", "--metrics", metric, "--group-by", group_by, "--csv", str(out)],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        with open(out, newline="") as f:
            rows = [r for r in csv.DictReader(f) if r.get(group_by)]
    return {normalize_key(r[group_by]): float(r[metric]) for r in rows if r[metric] != ""}


def query_expected(sql_file: str) -> dict:
    sql = (SQL_DIR / sql_file).read_text()
    with duckdb.connect(str(DATABASE), read_only=True) as con:
        rows = con.sql(sql).fetchall()
    return {normalize_key(key): float(value) for key, value in rows}


def compare(actual: dict, expected: dict) -> list:
    problems = []
    for key in sorted(set(actual) | set(expected)):
        if key not in actual:
            problems.append(f"{key}: missing from MetricFlow (expected {expected[key]})")
        elif key not in expected:
            problems.append(f"{key}: unexpected MetricFlow row ({actual[key]})")
        elif abs(actual[key] - expected[key]) > TOLERANCE:
            problems.append(f"{key}: MetricFlow {actual[key]} != expected {expected[key]}")
    return problems


def main() -> int:
    failed = 0
    for metric, group_by, sql_file in CHECKS:
        problems = compare(query_metricflow(metric, group_by), query_expected(sql_file))
        if problems:
            failed += 1
            print(f"FAIL  {metric} by {group_by}")
            for p in problems:
                print(f"        {p}")
        else:
            print(f"PASS  {metric} by {group_by}")
    print(f"\n{len(CHECKS) - failed} of {len(CHECKS)} reconciliation checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
