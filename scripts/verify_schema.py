from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple

from app.services.logger import log_job
from app.services.notion_schema_utils import ensure_all_schemas, ensure_schema, search_location_databases
from config import Config


async def _verify_single(db_id: str) -> Tuple[bool, List[str]]:
    changed, fields = await ensure_schema(db_id)
    return changed, fields


async def main() -> Dict[str, Any]:
    updated: List[str] = []
    skipped: List[str] = []
    failed: List[str] = []

    # Ensure configured DBs first
    for db_id in filter(None, [Config.LOCATIONS_MASTER_DB, Config.MEDICAL_FACILITIES_DB]):
        try:
            changed, _ = await _verify_single(db_id)
            if changed:
                updated.append(db_id)
            else:
                skipped.append(db_id)
        except Exception as exc:  # noqa: BLE001
            failed.append(db_id)
            log_job("schema_verify", "error", "error", f"db_id={db_id} error={exc}")

    # Discover production _Locations DBs
    try:
        discovered = await search_location_databases()
        for item in discovered:
            db_id = item.get("id")
            if not db_id:
                continue
            try:
                changed, _ = await _verify_single(db_id)
                if changed:
                    updated.append(db_id)
                else:
                    skipped.append(db_id)
            except Exception as exc:  # noqa: BLE001
                failed.append(db_id)
                log_job("schema_verify", "error", "error", f"db_id={db_id} error={exc}")
    except Exception as exc:  # noqa: BLE001
        log_job("schema_verify", "discover", "error", f"discover_failed: {exc}")

    return {"updated": updated, "skipped": skipped, "failed": failed}


if __name__ == "__main__":
    result = asyncio.run(main())
    print(result)
