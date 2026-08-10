select
    payment_id,
    order_id,
    payment_status,
    payment_method,
    currency,
    amount,
    event_time as payment_timestamp,
    processed_at
from {{ source('silver', 'payments') }}

