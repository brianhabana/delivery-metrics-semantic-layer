"""Generate fake customers and subscriptions seed CSVs.

Uses a fixed random seed so the output is identical on every run.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

START = date(2025, 11, 1)
AS_OF = date(2026, 10, 31)
DAYS = (AS_OF - START).days + 1
REGIONS = ["NA", "EMEA", "APAC", "LATAM"]
REGION_WEIGHTS = [45, 30, 15, 10]
N_CUSTOMERS = 700

customers = []
subscriptions = []
sub_id = 1

for cust_id in range(1, N_CUSTOMERS + 1):
    # Skew signups toward later dates so the business grows over the year.
    signup = START + timedelta(days=int(DAYS * random.random() ** 0.7))
    region = random.choices(REGIONS, REGION_WEIGHTS)[0]
    customers.append([cust_id, signup.isoformat(), region])

    # First subscription starts 0-14 days after signup.
    start = signup + timedelta(days=random.randint(0, 14))
    while start <= AS_OF:
        plan = "annual" if random.random() < 0.3 else "monthly"
        # Annual subscribers stay much longer on average than monthly ones.
        mean_days = 600 if plan == "annual" else 150
        end = start + timedelta(days=int(random.expovariate(1 / mean_days)))
        cancelled = end.isoformat() if end <= AS_OF else ""
        subscriptions.append([sub_id, cust_id, plan, start.isoformat(), cancelled])
        sub_id += 1

        # Some customers who cancel come back 2-12 weeks later.
        if not cancelled or random.random() > 0.35:
            break
        start = end + timedelta(days=random.randint(14, 90))

out = Path(__file__).resolve().parent.parent / "seeds"
out.mkdir(exist_ok=True)

with open(out / "customers.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["customer_id", "signup_date", "region"])
    writer.writerows(customers)

with open(out / "subscriptions.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["subscription_id", "customer_id", "plan", "started_at", "cancelled_at"])
    writer.writerows(subscriptions)

print(f"{len(customers)} customers, {len(subscriptions)} subscriptions")