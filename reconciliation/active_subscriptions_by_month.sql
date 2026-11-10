-- Expected active subscriptions at each month end.
-- Computed differently from the metric on purpose: instead of a running
-- total of starts minus cancellations, count subscriptions that had started
-- by month end and had not been cancelled by month end.
with months as (
    select cast(range as date) as period
    from range(date '2025-11-01', date '2026-11-01', interval 1 month)
)
select
    m.period,
    count(s.subscription_id) as expected
from months as m
left join main.stg_subscriptions as s
    on  s.started_at <= last_day(m.period)
    and (s.cancelled_at is null or s.cancelled_at > last_day(m.period))
group by 1
