"""Thin CLI wrapper to create a production from the PSL template."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root on path for service imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.services.create_production import CreateProductionError, create_production  # noqa: E402


def prompt_input(prompt_text: str) -> str:
    value = input(prompt_text).strip()
    if not value:
        print("[ERROR] Input cannot be empty.")
        sys.exit(1)
    return value


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    print("=== Create Production from Template ===")
    production_code = prompt_input("Production Code (e.g. TGD): ").upper()
    production_name = prompt_input("Production Name: ")

    try:
        result = create_production(production_code, production_name)
    except CreateProductionError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("[ERROR] Operation cancelled by user.")
        sys.exit(1)

    print("Success.")
    print(f"Production page ID: {result.get('production_page_id')}")
    print(f"New PSL database ID: {result.get('psl_database_id')}")
    print(f"New PSL database name: {result.get('psl_database_name')}")


if __name__ == "__main__":
    main()
