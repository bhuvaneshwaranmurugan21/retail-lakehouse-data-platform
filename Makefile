.PHONY: install lint test validate-contracts

install:
	python -m pip install -e ".[spark,dev]"

lint:
	python -m ruff check src spark_jobs scripts tests

test:
	python -m pytest

validate-contracts:
	python scripts/validate_contracts.py config/contracts

