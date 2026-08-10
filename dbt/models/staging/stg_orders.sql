with source as (
    select * from {{ source('silver', 'orders') }}
)

select
    order_id,
    customer_id,
    customer_email as customer_email_hash,
    store_id,
    order_status,
    currency,
    gross_amount,
    discount_amount,
    gross_amount - discount_amount as net_amount,
    event_time as order_timestamp,
    cast(event_time as date) as order_date,
    ingested_at,
    processed_at
from source

{% if is_incremental() %}
where processed_at > (select coalesce(max(processed_at), '1900-01-01') from {{ this }})
{% endif %}

