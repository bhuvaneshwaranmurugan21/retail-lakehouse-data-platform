{{ config(unique_key=['movement_date', 'location_id', 'sku'], incremental_strategy='delete+insert') }}

select
    movement_date,
    location_id,
    sku,
    sum(quantity_delta) as net_quantity_change,
    count(*) as movement_count,
    current_timestamp as refreshed_at
from {{ ref('stg_inventory_movements') }}
group by 1, 2, 3

