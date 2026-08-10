select
    movement_date,
    location_id,
    sku,
    count(*) as row_count
from {{ ref('fct_inventory_position') }}
group by 1, 2, 3
having count(*) > 1

