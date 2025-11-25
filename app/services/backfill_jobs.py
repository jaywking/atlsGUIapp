from __future__ import annotations

from typing import Any, Dict

from app.services.logger import log_job
from app.services.matching_service import match_to_master
from app.services.notion_locations import build_location_properties, fetch_and_cache_locations, fetch_location_pages_raw, normalize_location, resolve_status, update_location_page
from app.services.notion_medical_facilities import fetch_and_cache_medical_facilities
from app.services.location_status_utils import normalize_status_for_write


async def facilities_backfill_job() -> None:
    try:
        await fetch_and_cache_medical_facilities()
    except Exception as exc:  # noqa: BLE001
        log_job("jobs", "facilities_backfill", "error", f"Facilities backfill failed: {exc}")
        raise


async def locations_backfill_job() -> None:
    try:
        await fetch_and_cache_locations()
    except Exception as exc:  # noqa: BLE001
        log_job("jobs", "locations_backfill", "error", f"Locations backfill failed: {exc}")
        raise


async def backfill_structured_addresses() -> None:
    log_job("jobs", "locations_structured_backfill", "start", "Starting structured address backfill")
    try:
        pages = await fetch_location_pages_raw()
    except Exception as exc:  # noqa: BLE001
        log_job("jobs", "locations_structured_backfill", "error", f"Failed to fetch pages: {exc}")
        raise
    try:
        master_cache = await fetch_and_cache_locations()
    except Exception:
        master_cache = []

    stats = {"processed": 0, "updated": 0, "errors": 0, "unresolved": 0}
    for page in pages:
        stats["processed"] += 1
        page_id = page.get("id") or ""
        if not page_id:
            stats["errors"] += 1
            continue

        try:
            normalized = normalize_location(page)
            components: Dict[str, Any] = {
                "address1": normalized.get("address1"),
                "address2": normalized.get("address2"),
                "address3": normalized.get("address3"),
                "city": normalized.get("city"),
                "state": normalized.get("state"),
                "zip": normalized.get("zip"),
                "country": normalized.get("country"),
                "county": normalized.get("county"),
                "borough": normalized.get("borough"),
            }
            place_id = normalized.get("place_id")
            matched_flag = bool(normalized.get("locations_master_ids"))
            matched_master_id = normalized.get("locations_master_ids", [None])[0] if matched_flag else None
            if not matched_flag:
                match_result = match_to_master(
                    {
                        "id": normalized.get("id"),
                        "address1": normalized.get("address1"),
                        "city": normalized.get("city"),
                        "state": normalized.get("state"),
                        "zip": normalized.get("zip"),
                        "country": normalized.get("country"),
                        "place_id": normalized.get("place_id"),
                    },
                    master_cache,
                )
                matched_master_id = match_result.get("matched_master_id")
                matched_flag = bool(matched_master_id)
                if match_result.get("candidate_count", 0) > 1:
                    stats["unresolved"] += 1
                    log_job("matching", "multiple_candidates", "success", f"page_id={page_id} reason={match_result.get('match_reason')} count={match_result.get('candidate_count')}")
                elif matched_flag:
                    log_job("matching", "matched", "success", f"page_id={page_id} match_reason={match_result.get('match_reason')} matched_id={matched_master_id}")

            resolved_status = resolve_status(place_id=place_id, matched=matched_flag, explicit=normalized.get("status"))
            if resolved_status == "Unresolved":
                stats["unresolved"] += 1

            props = build_location_properties(
                components=components,
                production_id=normalized.get("production_id") or "",
                place_id=place_id,
                place_name=normalized.get("name"),
                latitude=normalized.get("latitude"),
                longitude=normalized.get("longitude"),
                status=resolved_status,
                matched=matched_flag,
                matched_master_id=matched_master_id,
            )
            await update_location_page(page_id, props)
            stats["updated"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["errors"] += 1
            log_job("jobs", "locations_structured_backfill", "error", f"page_id={page_id} error={exc}")
            continue

    try:
        await fetch_and_cache_locations()
    except Exception as exc:  # noqa: BLE001
        log_job("jobs", "locations_structured_backfill", "error", f"cache_refresh_failed: {exc}")

    log_job(
        "jobs",
        "locations_structured_backfill",
        "success",
        f"structured_backfill complete stats={stats}",
    )
