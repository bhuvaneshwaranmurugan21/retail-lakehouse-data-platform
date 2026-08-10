select
    return_id,
    order_id,
    sku,
    return_status,
    reason_code,
    quantity,
    refund_amount,
    event_time as return_timestamp,
    processed_at
from {{ source('silver', 'returns') }}

