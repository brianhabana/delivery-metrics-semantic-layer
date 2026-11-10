-- Expected net new per month: starts minus cancellations in the same month.
with starts as (
    select date_trunc('month', started_at) as period, count(*) as n
    from main.stg_subscriptions
    group by 1
),
cancels as (
    select date_trunc('month', cancelled_at) as period, count(*) as n
    from main.stg_subscriptions
    where cancelled_at is not null
    group by 1
)
select
    coalesce(s.period, c.period)            as period,
    coalesce(s.n, 0) - coalesce(c.n, 0)     as expected
from starts as s
full outer join cancels as c
    on s.period = c.period
