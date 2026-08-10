"""Validate every YAML source contract before pipeline deployment."""

from __future__ import annotations

import argparse

from retail_lakehouse.contracts import load_contract_directory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="Directory containing versioned YAML contracts")
    args = parser.parse_args()

    contracts = load_contract_directory(args.directory)
    for key, contract in contracts.items():
        print(f"validated {key} ({len(contract.fields)} fields, source={contract.source_system})")


if __name__ == "__main__":
    main()

