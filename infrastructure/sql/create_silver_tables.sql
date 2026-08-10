CREATE TABLE IF NOT EXISTS glue_catalog.silver.orders (
  event_id string,
  event_time timestamp,
  ingested_at timestamp,
  order_id string,
  customer_id string,
  customer_email string,
  store_id string,
  order_status string,
  currency string,
  gross_amount decimal(18,2),
  discount_amount decimal(18,2),
  event_date date,
  source_system string,
  contract_version int,
  processed_at timestamp
) USING iceberg
PARTITIONED BY (event_date)
TBLPROPERTIES ('format-version'='2', 'write.distribution-mode'='hash');

CREATE TABLE IF NOT EXISTS glue_catalog.silver.payments (
  event_id string,
  event_time timestamp,
  ingested_at timestamp,
  payment_id string,
  order_id string,
  payment_status string,
  payment_method string,
  currency string,
  amount decimal(18,2),
  event_date date,
  source_system string,
  contract_version int,
  processed_at timestamp
) USING iceberg
PARTITIONED BY (event_date)
TBLPROPERTIES ('format-version'='2', 'write.distribution-mode'='hash');

CREATE TABLE IF NOT EXISTS glue_catalog.silver.inventory_movements (
  event_id string,
  event_time timestamp,
  ingested_at timestamp,
  movement_id string,
  sku string,
  location_id string,
  movement_type string,
  quantity_delta int,
  event_date date,
  source_system string,
  contract_version int,
  processed_at timestamp
) USING iceberg
PARTITIONED BY (event_date)
TBLPROPERTIES ('format-version'='2', 'write.distribution-mode'='hash');

CREATE TABLE IF NOT EXISTS glue_catalog.silver.shipments (
  event_id string,
  event_time timestamp,
  ingested_at timestamp,
  shipment_id string,
  order_id string,
  carrier string,
  shipment_status string,
  promised_date date,
  delivered_at timestamp,
  event_date date,
  source_system string,
  contract_version int,
  processed_at timestamp
) USING iceberg
PARTITIONED BY (event_date)
TBLPROPERTIES ('format-version'='2', 'write.distribution-mode'='hash');

CREATE TABLE IF NOT EXISTS glue_catalog.silver.returns (
  event_id string,
  event_time timestamp,
  ingested_at timestamp,
  return_id string,
  order_id string,
  sku string,
  return_status string,
  reason_code string,
  quantity int,
  refund_amount decimal(18,2),
  event_date date,
  source_system string,
  contract_version int,
  processed_at timestamp
) USING iceberg
PARTITIONED BY (event_date)
TBLPROPERTIES ('format-version'='2', 'write.distribution-mode'='hash');

