{{ config(unique_key=['order_date', 'store_id', 'currency'], incremental_strategy='delete+insert') }}

select
    order_date,
    store_id,
    currency,
    count(distinct order_id) as order_count,
    sum(gross_amount) as gross_sales,
    sum(discount_amount) as discount_amount,
    sum(net_amount) as net_sales,
    current_timestamp as refreshed_at
from {{ ref('stg_orders') }}
where order_status in ('PAID', 'FULFILLED', 'RETURNED')
{% if is_incremental() %}
  and order_date >= dateadd(day, -3, current_date)
{% endif %}
group by 1, 2, 3
