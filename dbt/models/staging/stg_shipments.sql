select
    shipment_id,
    order_id,
    carrier,
    shipment_status,
    promised_date,
    delivered_at,
    event_time as shipment_created_at,
    processed_at
from {{ source('silver', 'shipments') }}

