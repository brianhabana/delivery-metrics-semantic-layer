# Metric Spec: Subscription Growth & Retention

## Business question

A creative software app sells monthly and annual subscriptions. Leadership wants to know:
**is the subscriber base growing, and are new subscribers sticking around?**

All data in this repo is fictional.

## Reporting period

- Data covers **2025-11-01 through 2026-10-31** (12 months).
- **As-of date:** 2026-10-31. Used to decide which subscriptions are old enough to judge retention.

## Source tables

### `customers` (one row per customer)

| Column | Description |
|---|---|
| customer_id | Unique customer identifier |
| signup_date | Date the customer created an account |
| region | `NA`, `EMEA`, `APAC`, `LATAM` |

### `subscriptions` (one row per subscription; a customer can have more than one over time)

| Column | Description |
|---|---|
| subscription_id | Unique subscription identifier |
| customer_id | Customer who owns the subscription |
| plan | `monthly` or `annual` |
| started_at | Date the paid subscription started |
| cancelled_at | Date the subscription ended; empty if still active |

## Metrics

### 1. new_subscriptions
- **Definition:** Count of subscriptions, dated by `started_at`.

### 2. cancellations
- **Definition:** Count of subscriptions with a `cancelled_at`, dated by `cancelled_at`.

### 3. net_new_subscriptions
- **Definition:** `new_subscriptions − cancellations` for the same period.
- **Reading it:** Positive means the base grew that period.

### 4. active_subscriptions
- **Definition:** Running total of all subscriptions started minus all subscriptions cancelled, up to and including the period.
- **Note:** A point-in-time balance, like a bank balance. It is not summed across periods.

### 5. retention_rate_90d
- **Definition:** Subscriptions still active 90 days after `started_at` ÷ subscriptions eligible to be judged.
- **Still active at 90 days:** `cancelled_at` is empty, or `cancelled_at` ≥ `started_at` + 90 days.
- **Eligible:** `started_at` ≤ as-of date − 90 days. Newer subscriptions are excluded because they haven't had 90 days yet; counting them would make retention look better than it is.
- **Dated by:** `started_at` (the starting cohort).

## Dimensions

| Dimension | Source |
|---|---|
| plan | subscriptions.plan |
| region | customers.region |
| time (day / week / month) | `started_at` or `cancelled_at`, per metric above |

## Business rules

1. Every subscription belongs to a known customer.
2. `cancelled_at`, when present, is on or after `started_at`.
3. A subscription cannot start before the customer's `signup_date`.

## Acceptance criteria

- Each metric, queried by month and by plan, matches an independently hand-written SQL query exactly.
- IDs are unique and non-null; `plan` and `region` contain only the listed values.
