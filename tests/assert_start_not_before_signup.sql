-- Business rule 3: a subscription cannot start before the customer signed up.
-- Returns offending rows; the test passes when zero rows come back.
select s.*
from {{ ref('stg_subscriptions') }} as s
join {{ ref('stg_customers') }} as c
    on s.customer_id = c.customer_id
where s.started_at < c.signup_date
