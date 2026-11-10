-- Business rule 2: a subscription cannot be cancelled before it starts.
-- Returns offending rows; the test passes when zero rows come back.
select *
from {{ ref('stg_subscriptions') }}
where cancelled_at < started_at
