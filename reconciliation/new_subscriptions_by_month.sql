-- Expected new_subscriptions per month, counted straight from staging.
select
    date_trunc('month', started_at) as period,
    count(*)                        as expected
from main.stg_subscriptions
group by 1
