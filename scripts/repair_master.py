from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from app.services.ingestion_normalizer import normalize_ingest_record
from app.services.logger import log_job
from app.services.notion_locations import get_locations_master_cached, update_location_page


def _rt(value: str) -> Dict[str, Any]:
    return {"rich_text": [{"text": {"content": value}}]}


def _num(value: float | None) -> Dict[str, Any]:
    return {"number": value}


def _build_updates(normalized: Dict[str, Any]) -> Dict[str, Any]:
    comps = normalized.get("components") or {}
    props: Dict[str, Any] = {
        "address1": _rt(comps.get("address1") or ""),
        "address2": _rt(comps.get("address2") or ""),
        "address3": _rt(comps.get("address3") or ""),
        "city": _rt(comps.get("city") or ""),
        "state": _rt(comps.get("state") or ""),
        "zip": _rt(comps.get("zip") or ""),
        "country": _rt(comps.get("country") or ""),
        "county": _rt(comps.get("county") or ""),
        "borough": _rt(comps.get("borough") or ""),
        "Full Address": _rt(normalized.get("full_address") or ""),
        "Place_ID": _rt(normalized.get("place_id") or ""),
    }
    if normalized.get("formatted_address_google"):
        props["formatted_address_google"] = _rt(normalized.get("formatted_address_google") or "")
    if normalized.get("latitude") is not None:
        props["Latitude"] = _num(normalized.get("latitude"))
    if normalized.get("longitude") is not None:
        props["Longitude"] = _num(normalized.get("longitude"))
    return props


async def rebuild_master() -> Dict[str, Any]:
    rows = await get_locations_master_cached(refresh=True)
    stats = {"processed": 0, "updated": 0, "errors": 0}

    for row in rows:
        stats["processed"] += 1
        try:
            normalized = normalize_ingest_record(row, production_id=row.get("production_id") or "", log_category="master_rebuild")
            updates = _build_updates(normalized)
            await update_location_page(row.get("id") or "", updates)
            stats["updated"] += 1
            log_job("master_rebuild", "update", "success", f"row_id={row.get('id')} updated_fields={list(updates.keys())}")
        except Exception as exc:  # noqa: BLE001
            stats["errors"] += 1
            log_job("master_rebuild", "update", "error", f"row_id={row.get('id')} error={exc}")
    return stats


if __name__ == "__main__":
    result = asyncio.run(rebuild_master())
    print(result)
