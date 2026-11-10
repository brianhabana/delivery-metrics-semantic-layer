select
    cast(customer_id as integer) as customer_id,
    cast(signup_date as date)    as signup_date,
    upper(trim(region))          as region
from {{ ref('customers') }}