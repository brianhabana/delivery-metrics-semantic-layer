# Subscription Metrics Semantic Layer

![ci](https://github.com/brianhabana/delivery-metrics-semantic-layer/actions/workflows/ci.yml/badge.svg)

A small, complete example of the semantic-layer workflow: **a plain-English metric spec, translated into declarative YAML (dbt + MetricFlow), validated by four layers of automated tests, and run end to end in CI on every push.**

The scenario is a fictional creative-software company asking two questions: *is the subscriber base growing, and are new subscribers sticking around?* All data is generated and fictional.

## The workflow

| Step | What happens | Where |
|---|---|---|
| 1. Spec | Metrics, dimensions, business rules and acceptance criteria written in plain English, the way a stakeholder would hand them over | [`specs/metric_specs.md`](specs/metric_specs.md) |
| 2. Data | Reproducible fake data (fixed random seed) loaded as raw tables | [`scripts/generate_seeds.py`](scripts/generate_seeds.py), [`seeds/`](seeds/) |
| 3. Staging | One cleanup model per source: explicit types, standardized text | [`models/staging/`](models/staging/) |
| 4. Mart | One row per subscription; each spec business rule encoded once as a 1/0 flag | [`models/marts/fct_subscriptions.sql`](models/marts/fct_subscriptions.sql) |
| 5. Semantic layer | Entities, dimensions and metrics declared in YAML | [`models/marts/fct_subscriptions.yml`](models/marts/fct_subscriptions.yml) |
| 6. Tests | Four layers, from YAML syntax to metric-level reconciliation | see below |
| 7. CI | All four layers run on every push and pull request | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |

## Metrics

| Metric | Type | Definition |
|---|---|---|
| `new_subscriptions` | simple | Subscriptions started, dated by start date |
| `cancellations` | simple | Subscriptions cancelled, dated by cancel date |
| `net_new_subscriptions` | derived | `new_subscriptions − cancellations` |
| `active_subscriptions` | derived from cumulative | Running balance at period end: all starts to date minus all cancellations to date |
| `retention_rate_90d` | ratio | Subscriptions still active 90 days after starting ÷ subscriptions old enough to judge |

Dimensions: `plan` (monthly / annual), `region`, and time at day / week / month / year.

Helper metrics (running totals and flag sums) are marked `hidden: true`, so only the five spec metrics are exposed to consumers.

## Testing: four layers

| Layer | Check | What it catches |
|---|---|---|
| 1 | `yamllint` | Malformed or inconsistently indented YAML |
| 2 | `dbt build` (14 data tests) | Duplicate or missing IDs, unexpected category values, orphaned subscriptions, and the spec's business rules (no cancel before start, no start before signup) |
| 3 | `mf validate-configs` | Invalid semantic definitions, plus every dimension, entity and metric checked against the actual warehouse |
| 4 | [`scripts/reconcile.py`](scripts/reconcile.py) | Each metric queried through MetricFlow and compared row by row against an independent hand-written query in [`reconciliation/`](reconciliation/) |

The reconciliation queries deliberately use **different logic** from the metric where possible. For example, `active_subscriptions` is checked by counting subscriptions that had started and not yet cancelled at each month end, instead of repeating the running-total math. Retention is recomputed from staging rather than from the mart's flags, so the mart's logic is verified too. The check was confirmed to fail, with a non-zero exit, when an expected definition is altered.

## Sample output

```
$ mf query --metrics retention_rate_90d --group-by subscription__plan

subscription__plan      retention_rate_90d
annual                            0.908497
monthly                           0.548485
```

```
$ mf query --metrics new_subscriptions,cancellations,net_new_subscriptions,active_subscriptions \
           --group-by metric_time__month --order metric_time__month

metric_time__month   new_subscriptions  cancellations  net_new_subscriptions  active_subscriptions
2025-11-01                          11              1                     10                    10
...
2026-10-01                         101             57                     44                   419
```

Add `--explain` to any query to see the SQL MetricFlow generates.

## Run it locally

Requires Python 3.13.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

yamllint .                         # layer 1
dbt build                          # layer 2: seeds, models, data tests
mf validate-configs                # layer 3
python scripts/reconcile.py        # layer 4

mf query --metrics retention_rate_90d --group-by subscription__plan
```

No credentials are needed. Everything runs against a local DuckDB file.

## Design notes

- **Warehouse portability.** DuckDB stands in for a cloud warehouse. Only `profiles.yml` is warehouse-specific; the models, metric definitions and tests do not change when it points at Databricks, Snowflake or BigQuery.
- **Seeds stand in for the raw layer.** In production, staging models would read ingested tables via `{{ source() }}` instead of `{{ ref() }}` on seeds. That is a one-line change per staging model and nothing above staging changes. Seeds keep this repo runnable anywhere, including CI, with deterministic results.
- **Business logic lives in one place.** Spec rules such as 90-day retention eligibility are encoded once in the mart as flags; metrics only aggregate them. Retention excludes subscriptions too new to judge as of the reporting date (`as_of_date` var, default 2026-10-31), so recent cohorts don't inflate the rate.
- **Current semantic-layer spec.** Uses the dbt 1.12 YAML format, with semantic models declared on the model and measures folded into simple metrics, validated with MetricFlow 0.15.
- **Open Semantic Interchange export.** `dbt build` also writes `target/osi_document.json`, an OSI-format export of the semantic model and public metrics, so the same definitions can be consumed by other OSI-compatible tools. Note that running-total semantics (`active_subscriptions`) are flattened in that export.
- **Pinned versions.** [`requirements.txt`](requirements.txt) pins every tool so local runs and CI use identical versions.

## Project structure

```
specs/metric_specs.md        plain-English metric spec
scripts/generate_seeds.py    reproducible fake data generator
seeds/                       customers.csv, subscriptions.csv
models/staging/              stg_customers, stg_subscriptions + data tests
models/marts/                fct_subscriptions (.sql model, .yml semantic layer)
models/metricflow_time_spine daily calendar used for running totals
tests/                       business-rule data tests
reconciliation/              hand-written expected values per metric
scripts/reconcile.py         compares MetricFlow output to reconciliation queries
.github/workflows/ci.yml     runs all four test layers
```
