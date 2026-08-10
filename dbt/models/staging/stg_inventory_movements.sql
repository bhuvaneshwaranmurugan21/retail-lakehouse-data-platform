select
    movement_id,
    sku,
    location_id,
    movement_type,
    quantity_delta,
    event_time as movement_timestamp,
    cast(event_time as date) as movement_date,
    processed_at
from {{ source('silver', 'inventory_movements') }}

