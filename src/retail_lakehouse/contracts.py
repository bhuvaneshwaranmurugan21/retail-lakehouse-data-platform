"""Load and validate versioned source contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SUPPORTED_TYPES = {
    "boolean",
    "date",
    "decimal(18,2)",
    "integer",
    "long",
    "string",
    "timestamp",
}
SUPPORTED_PII_ACTIONS = {"drop", "sha256"}


class ContractError(ValueError):
    """Raised when a source contract is incomplete or internally inconsistent."""


@dataclass(frozen=True)
class FieldContract:
    name: str
    data_type: str
    required: bool = False
    allowed_values: tuple[str, ...] = ()
    minimum: float | None = None
    pii_action: str | None = None


@dataclass(frozen=True)
class DatasetContract:
    dataset: str
    version: int
    source_system: str
    event_id: str
    event_time: str
    business_keys: tuple[str, ...]
    partition_by: tuple[str, ...]
    fields: tuple[FieldContract, ...]

    @property
    def field_names(self) -> set[str]:
        return {field.name for field in self.fields}


def _require(mapping: dict[str, Any], key: str, context: str) -> Any:
    value = mapping.get(key)
    if value in (None, "", []):
        raise ContractError(f"{context}: missing required value '{key}'")
    return value


def _parse_field(raw: dict[str, Any], context: str) -> FieldContract:
    name = str(_require(raw, "name", context))
    data_type = str(_require(raw, "type", context)).lower()
    if data_type not in SUPPORTED_TYPES:
        raise ContractError(f"{context}.{name}: unsupported type '{data_type}'")

    allowed_values = tuple(str(value) for value in raw.get("allowed_values", []))
    pii_action = raw.get("pii_action")
    if pii_action is not None and pii_action not in SUPPORTED_PII_ACTIONS:
        raise ContractError(f"{context}.{name}: unsupported pii_action '{pii_action}'")

    minimum = raw.get("minimum")
    if minimum is not None and not isinstance(minimum, int | float):
        raise ContractError(f"{context}.{name}: minimum must be numeric")

    return FieldContract(
        name=name,
        data_type=data_type,
        required=bool(raw.get("required", False)),
        allowed_values=allowed_values,
        minimum=float(minimum) if minimum is not None else None,
        pii_action=pii_action,
    )


def parse_contract(raw: dict[str, Any], source: str = "contract") -> DatasetContract:
    """Parse one YAML mapping and enforce the contract's structural invariants."""

    dataset = str(_require(raw, "dataset", source))
    version = _require(raw, "version", source)
    if not isinstance(version, int) or version < 1:
        raise ContractError(f"{source}: version must be a positive integer")

    raw_fields = _require(raw, "fields", source)
    if not isinstance(raw_fields, list):
        raise ContractError(f"{source}: fields must be a list")

    fields = tuple(_parse_field(field, f"{dataset}.fields") for field in raw_fields)
    field_names = [field.name for field in fields]
    duplicates = sorted({name for name in field_names if field_names.count(name) > 1})
    if duplicates:
        raise ContractError(f"{source}: duplicate fields: {', '.join(duplicates)}")

    contract = DatasetContract(
        dataset=dataset,
        version=version,
        source_system=str(_require(raw, "source_system", source)),
        event_id=str(_require(raw, "event_id", source)),
        event_time=str(_require(raw, "event_time", source)),
        business_keys=tuple(str(key) for key in _require(raw, "business_keys", source)),
        partition_by=tuple(str(key) for key in _require(raw, "partition_by", source)),
        fields=fields,
    )

    referenced = {contract.event_id, contract.event_time, *contract.business_keys}
    missing = sorted(referenced - contract.field_names)
    if missing:
        raise ContractError(f"{source}: referenced fields are not declared: {', '.join(missing)}")

    required_names = {field.name for field in fields if field.required}
    missing_required = sorted(referenced - required_names)
    if missing_required:
        raise ContractError(
            f"{source}: identity and time fields must be required: {', '.join(missing_required)}"
        )

    return contract


def load_contract(path: str | Path) -> DatasetContract:
    contract_path = Path(path)
    with contract_path.open(encoding="utf-8") as stream:
        raw = yaml.safe_load(stream)
    if not isinstance(raw, dict):
        raise ContractError(f"{contract_path}: contract root must be a mapping")
    return parse_contract(raw, str(contract_path))


def load_contract_directory(directory: str | Path) -> dict[str, DatasetContract]:
    """Load all contracts and reject duplicate dataset/version registrations."""

    contracts: dict[str, DatasetContract] = {}
    for path in sorted(Path(directory).glob("*.yaml")):
        contract = load_contract(path)
        registry_key = f"{contract.dataset}:v{contract.version}"
        if registry_key in contracts:
            raise ContractError(f"duplicate contract registration: {registry_key}")
        contracts[registry_key] = contract
    if not contracts:
        raise ContractError(f"no YAML contracts found in {directory}")
    return contracts

