{{ config(unique_key='order_id', incremental_strategy='delete+insert') }}

with captured_payments as (
    select
        order_id,
        sum(case when payment_status = 'CAPTURED' then amount else 0 end) as captured_amount
    from {{ ref('stg_payments') }}
    group by 1
),
latest_shipment as (
    select *
    from (
        select
            *,
            row_number() over (partition by order_id order by processed_at desc) as row_number
        from {{ ref('stg_shipments') }}
    ) ranked
    where row_number = 1
),
returns as (
    select
        order_id,
        sum(case when return_status in ('RECEIVED', 'REFUNDED') then refund_amount else 0 end)
            as refund_amount
    from {{ ref('stg_returns') }}
    group by 1
)

select
    orders.order_id,
    orders.store_id,
    orders.order_status,
    orders.net_amount,
    coalesce(payments.captured_amount, 0) as captured_amount,
    coalesce(returns.refund_amount, 0) as refund_amount,
    shipments.carrier,
    shipments.shipment_status,
    shipments.promised_date,
    shipments.delivered_at,
    datediff(minute, orders.order_timestamp, shipments.delivered_at) as fulfillment_minutes,
    current_timestamp as refreshed_at
from {{ ref('stg_orders') }} orders
left join captured_payments payments using (order_id)
left join latest_shipment shipments using (order_id)
left join returns using (order_id)

