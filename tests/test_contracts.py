from __future__ import annotations

import pytest

from retail_lakehouse.contracts import ContractError, load_contract_directory, parse_contract


def test_contract_registry_loads_all_retail_domains() -> None:
    registry = load_contract_directory("config/contracts")

    assert set(registry) == {
        "inventory_movements:v1",
        "orders:v1",
        "payments:v1",
        "returns:v1",
        "shipments:v1",
    }
    assert registry["orders:v1"].business_keys == ("order_id",)


def test_contract_rejects_an_identity_field_that_is_nullable() -> None:
    raw = {
        "dataset": "orders",
        "version": 1,
        "source_system": "order-service",
        "event_id": "event_id",
        "event_time": "event_time",
        "business_keys": ["order_id"],
        "partition_by": ["event_date"],
        "fields": [
            {"name": "event_id", "type": "string", "required": True},
            {"name": "event_time", "type": "timestamp", "required": True},
            {"name": "order_id", "type": "string", "required": False},
        ],
    }

    with pytest.raises(ContractError, match="must be required"):
        parse_contract(raw)


def test_contract_rejects_duplicate_fields() -> None:
    raw = {
        "dataset": "orders",
        "version": 1,
        "source_system": "order-service",
        "event_id": "event_id",
        "event_time": "event_time",
        "business_keys": ["order_id"],
        "partition_by": ["event_date"],
        "fields": [
            {"name": "event_id", "type": "string", "required": True},
            {"name": "event_id", "type": "string", "required": True},
            {"name": "event_time", "type": "timestamp", "required": True},
            {"name": "order_id", "type": "string", "required": True},
        ],
    }

    with pytest.raises(ContractError, match="duplicate fields"):
        parse_contract(raw)

