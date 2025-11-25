from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

from app.services.address_parser import parse_address
from app.services.logger import log_job
from app.services.notion_locations import build_location_properties, create_location_page, fetch_and_cache_locations, update_location_page
from app.services.matching_service import match_to_master
from app.services.notion_locations import resolve_status

VALID_DUPLICATE_STRATEGIES = {"skip", "update", "flag"}


def _normalize_address(address: str) -> str:
    return " ".join(address.lower().split()) if address else ""


def _parsed_key(parsed: Dict[str, Any]) -> str:
    parts = [parsed.get("address1"), parsed.get("city"), parsed.get("state"), parsed.get("zip"), parsed.get("country")]
    cleaned = [str(part).strip().lower() for part in parts if part]
    return "|".join(cleaned)


def _build_existing_indexes(records: List[Dict[str, Any]], production_id: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    by_full: Dict[str, Dict[str, Any]] = {}
    by_parsed: Dict[str, Dict[str, Any]] = {}
    prod_lower = (production_id or "").lower()

    for record in records:
        if (record.get("production_id") or "").lower() != prod_lower:
            continue

        address = record.get("address") or ""
        normalized = _normalize_address(address)
        parsed_key = _parsed_key(parse_address(address))
        entry = {
            "id": record.get("id") or record.get("row_id") or "",
            "address": address,
            "production_id": record.get("production_id") or "",
        }
        if normalized:
            by_full.setdefault(normalized, entry)
        if parsed_key:
            by_parsed.setdefault(parsed_key, entry)

    return by_full, by_parsed


async def _geocode_address(_: str) -> Tuple[float | None, float | None, str | None]:
    # Placeholder for future geocoding integration (v0.8.x+). Returns (lat, lng, place_name).
    return None, None, None


async def _ensure_production_link(page_id: str, production_id: str) -> None:
    if not page_id:
        raise ValueError("Missing page_id for update")
    properties = {"ProductionID": {"rich_text": [{"text": {"content": production_id}}]}}
    await update_location_page(page_id, properties)


async def _create_location_record(address: str, production_id: str, flag_duplicate: bool, match_result: Dict[str, Any], parsed: Dict[str, Any]) -> Dict[str, Any]:
    latitude, longitude, place_name = await _geocode_address(address)
    matched_id = match_result.get("matched_master_id")
    normalized_status = resolve_status(place_id=None, matched=bool(matched_id), explicit=match_result.get("status"))
    properties = build_location_properties(
        components=parsed,
        production_id=production_id,
        place_id=None,
        place_name=place_name,
        latitude=latitude,
        longitude=longitude,
        status=normalized_status,
        matched=bool(matched_id),
        matched_master_id=matched_id,
    )
    if flag_duplicate:
        note_text = f"Potential duplicate flagged for production {production_id}"
        properties["Notes"] = {"rich_text": [{"text": {"content": note_text[:2000]}}]}
    try:
        return await create_location_page(properties)
    except Exception:
        if flag_duplicate and "Notes" in properties:
            properties.pop("Notes", None)
            return await create_location_page(properties)
        raise


async def import_locations_for_production(production_id: str, addresses: List[str], duplicate_strategy: str = "skip") -> None:
    strategy = duplicate_strategy if duplicate_strategy in VALID_DUPLICATE_STRATEGIES else "skip"
    cleaned_addresses = [str(addr).strip() for addr in addresses if isinstance(addr, str) and str(addr).strip()]
    skipped_empty = len(addresses) - len(cleaned_addresses)

    log_job(
        "locations_batch_import",
        "start",
        "start",
        f"production_id={production_id} address_count={len(cleaned_addresses)} strategy={strategy}",
    )
    started = time.perf_counter()

    try:
        existing = await fetch_and_cache_locations()
    except Exception as exc:  # noqa: BLE001
        log_job("locations_batch_import", "prefetch", "error", f"prefetch_failed: {exc}")
        existing = []
    master_cache = existing

    by_full, by_parsed = _build_existing_indexes(existing, production_id)

    stats = {
        "processed": 0,
        "created": 0,
        "duplicates": 0,
        "updated": 0,
        "flagged": 0,
        "errors": 0,
        "skipped_empty": skipped_empty,
    }

    for address in cleaned_addresses:
        stats["processed"] += 1
        normalized = _normalize_address(address)
        parsed = parse_address(address)
        parsed_key = _parsed_key(parsed)
        match_result = match_to_master(
            {
                "id": "",
                "address1": parsed.get("address1"),
                "city": parsed.get("city"),
                "state": parsed.get("state"),
                "zip": parsed.get("zip"),
                "country": parsed.get("country"),
                "place_id": None,
            },
            master_cache,
        )
        if match_result.get("candidate_count", 0) > 1:
            log_job("matching", "multiple_candidates", "success", f"address={normalized} reason={match_result.get('match_reason')} count={match_result.get('candidate_count')}")
        elif match_result.get("matched_master_id"):
            log_job("matching", "matched", "success", f"address={normalized} match_reason={match_result.get('match_reason')} matched_id={match_result.get('matched_master_id')}")

        duplicate = None
        if normalized and normalized in by_full:
            duplicate = by_full[normalized]
        elif parsed_key and parsed_key in by_parsed:
            duplicate = by_parsed[parsed_key]

        flag_duplicate = False
        if duplicate:
            stats["duplicates"] += 1
            if strategy == "skip":
                continue
            if strategy == "update":
                try:
                    await _ensure_production_link(duplicate.get("id") or "", production_id)
                    stats["updated"] += 1
                except Exception as exc:  # noqa: BLE001
                    stats["errors"] += 1
                    log_job(
                        "locations_batch_import",
                        "update",
                        "error",
                        f"production_id={production_id} address={normalized} error={exc}",
                    )
                continue
            if strategy == "flag":
                flag_duplicate = True

        try:
            page = await _create_location_record(address, production_id, flag_duplicate, match_result, parsed)
            stats["created"] += 1
            if flag_duplicate:
                stats["flagged"] += 1
            entry = {"id": page.get("id") if isinstance(page, dict) else "", "address": address, "production_id": production_id}
            if normalized:
                by_full.setdefault(normalized, entry)
            if parsed_key:
                by_parsed.setdefault(parsed_key, entry)
            # Placeholder: trigger facility lookups for new locations in a future milestone.
        except Exception as exc:  # noqa: BLE001
            stats["errors"] += 1
            log_job(
                "locations_batch_import",
                "create",
                "error",
                f"production_id={production_id} address={normalized} error={exc}",
            )
            continue

    try:
        await fetch_and_cache_locations()
    except Exception as exc:  # noqa: BLE001
        log_job("locations_batch_import", "cache_refresh", "error", f"post_import_cache_refresh_failed: {exc}")

    duration_ms = int((time.perf_counter() - started) * 1000)
    log_job(
        "locations_batch_import",
        "complete",
        "success",
        f"production_id={production_id} strategy={strategy} duration_ms={duration_ms} stats={stats}",
    )
