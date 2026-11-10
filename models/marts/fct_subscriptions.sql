-- fct_subscriptions
-- One row per subscription. Joins subscriptions to customers and turns each
-- business rule from specs/metric_specs.md into a 1/0 flag, so the metric
-- YAML only has to sum flags instead of re-implementing the logic.

-- Reporting as-of date. Override at run time with:
--   dbt run --vars '{as_of_date: "2026-12-31"}'
{% set as_of_date = var('as_of_date', '2026-10-31') %}

-- Inputs: the two cleaned staging models
with subscriptions as (
    select * from {{ ref('stg_subscriptions') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
)

select
    -- Columns passed through from staging
    s.subscription_id,
    s.customer_id,
    s.plan,
    c.region,
    s.started_at,
    s.cancelled_at,

    -- Has this subscription been cancelled?
    case when s.cancelled_at is not null then 1 else 0 end as is_cancelled,

    -- Old enough to judge 90-day retention?
    -- (started at least 90 days before the as-of date)
    case
        when s.started_at <= date '{{ as_of_date }}' - interval 90 day then 1
        else 0
    end as is_eligible_90d,

    -- Retained at 90 days?
    -- (eligible AND still active, or cancelled on/after day 90)
    case
        when s.started_at <= date '{{ as_of_date }}' - interval 90 day
         and (s.cancelled_at is null or s.cancelled_at >= s.started_at + interval 90 day)
        then 1
        else 0
    end as is_retained_90d

from subscriptions as s
-- Look up each subscription's customer to get region. Left join keeps every
-- subscription; a relationships test flags any with no matching customer.
left join customers as c
    on s.customer_id = c.customer_id
