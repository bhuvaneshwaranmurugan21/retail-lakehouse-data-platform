.PHONY: install lint test validate-contracts run-sample

install:
	python -m pip install -e ".[spark,dev]"

lint:
	python -m ruff check src spark_jobs scripts tests

test:
	python -m pytest

validate-contracts:
	python scripts/validate_contracts.py config/contracts

run-sample:
	SPARK_LOCAL_IP=127.0.0.1 python spark_jobs/bronze_to_silver.py \
		--contract config/contracts/orders_v1.yaml \
		--input examples/orders.jsonl \
		--silver-path data/silver/orders \
		--quarantine data/quarantine/orders

