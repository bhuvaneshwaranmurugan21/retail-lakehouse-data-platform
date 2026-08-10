select
    order_date,
    store_id,
    currency,
    count(*) as row_count
from {{ ref('fct_daily_sales') }}
group by 1, 2, 3
having count(*) > 1

