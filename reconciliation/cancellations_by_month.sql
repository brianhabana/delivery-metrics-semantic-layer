-- Expected cancellations per month, dated by cancel date.
select
    date_trunc('month', cancelled_at) as period,
    count(*)                          as expected
from main.stg_subscriptions
where cancelled_at is not null
group by 1
