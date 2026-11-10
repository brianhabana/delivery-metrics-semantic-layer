select
    cast(subscription_id as integer) as subscription_id,
    cast(customer_id as integer)     as customer_id,
    lower(trim(plan))                as plan,
    cast(started_at as date)         as started_at,
    cast(cancelled_at as date)       as cancelled_at
from {{ ref('subscriptions') }}