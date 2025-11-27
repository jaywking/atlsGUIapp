import time
from typing import Any, Dict, List

from fastapi import APIRouter, Query

from app.services.cache_utils import DEFAULT_MAX_AGE_SECONDS, is_cache_stale
from app.services.logger import log_job
from app.services.matching_service import match_to_master
from app.services.notion_locations import (
    fetch_all_locations,
    fetch_and_cache_locations,
    get_cached_locations,
    get_locations_master_cached,
    load_all_production_locations,
    load_locations_master,
    search_locations,
    update_location_page,
    resolve_status,
)
from app.services.validation_service import validate_links
from config import Config
from scripts import process_new_locations

print("DEBUG: locations_api imported successfully")

router = APIRouter(prefix="/api/locations", tags=["locations"])


async def _load_locations(max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS) -> tuple[List[Dict[str, Any]], str]:
    cache = await get_cached_locations(max_age_seconds=max_age_seconds)
    normalized = cache.get("normalized") if isinstance(cache, dict) else None
    if isinstance(normalized, list) and not is_cache_stale(cache, max_age_seconds=max_age_seconds):
        return normalized, "cache"

    log_job("locations", "cache_refresh", "start", "operation=locations_cache_refresh reason=stale_or_missing")
    locations = await fetch_and_cache_locations()
    return locations, "refreshed"


def _run_location_job() -> dict:
    try:
        result = process_new_locations.main()
        message = str(result)
        log_job(category="locations", action="process", status="success", message=message)
        return {"status": "success", "message": message}
    except Exception as exc:  # noqa: BLE001
        err = str(exc)
        log_job(category="locations", action="process", status="error", message=err)
        return {"status": "error", "message": err}


@router.post("/process")
def process_locations() -> dict:
    return _run_location_job()


@router.get("/list")
async def list_locations() -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        locations, source = await _load_locations()
    except Exception as exc:  # noqa: BLE001
        err = f"Unable to load locations: {exc}"
        log_job("locations", "list", "error", err)
        return {"status": "error", "message": err}

    duration_ms = int((time.perf_counter() - started) * 1000)
    message = f"Returned {len(locations)} locations in {duration_ms} ms source={source}"
    log_job("locations", "list", "success", message)
    return {
        "status": "success",
        "message": message,
        "data": {"items": locations, "total": len(locations)},
    }


def _validate_limit(limit: int, default: int = 1000, max_limit: int = 10_000) -> int:
    if limit is None:
        return default
    if limit < 1 or limit > max_limit:
        raise ValueError(f"limit must be between 1 and {max_limit}")
    return limit


@router.get("/all")
async def all_locations(limit: int = 1000, refresh: bool = Query(False)) -> Dict[str, Any]:
    try:
        validated_limit = _validate_limit(limit)
    except ValueError as exc:
        err = f"Invalid limit: {exc}"
        log_job("locations", "all", "error", err)
        return {"status": "error", "message": err, "data": []}

    productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    if not productions_db_id:
        err = "Missing productions master database id"
        log_job("locations", "all", "error", err)
        return {"status": "error", "message": err, "data": []}

    started = time.perf_counter()
    log_job("locations", "all", "start", f"operation=locations_bulk_retrieval limit={validated_limit} refresh={refresh}")
    try:
        records = await load_all_production_locations(productions_db_id, refresh=refresh)
    except Exception as exc:  # noqa: BLE001
        err = f"Unable to load production locations: {exc}"
        log_job("locations", "all", "error", f"{err}; limit={validated_limit}")
        return {"status": "error", "message": err, "data": []}

    sliced = records[:validated_limit]
    duration_ms = int((time.perf_counter() - started) * 1000)
    message = f"Returned {len(sliced)} production locations in {duration_ms} ms (limit {validated_limit})"
    log_job("locations", "all", "success", message)
    return {"status": "success", "message": message, "data": sliced}


@router.get("/master")
async def get_master_locations() -> Dict[str, Any]:
    try:
        master = await get_locations_master_cached(refresh=True)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load master locations: {exc}"
        log_job("locations", "master", "error", err)
        return {"status": "error", "message": err}

    return {
        "status": "success",
        "message": f"Returned {len(master)} master locations",
        "data": master,
    }


@router.get("/find")
async def find_locations(
    name_contains: str | None = None,
    address_contains: str | None = None,
    city: str | None = None,
    state: str | None = None,
    production_id: str | None = None,
    sort: str | None = None,
) -> Dict[str, Any]:
    filters = {
        "name_contains": name_contains or "",
        "address_contains": address_contains or "",
        "city": city or "",
        "state": state or "",
        "production_id": production_id or "",
    }
    sorts = [sort] if sort else []

    search_started = time.perf_counter()
    log_job("locations", "find", "start", f"Locations search params={filters}, sort={sorts}")

    try:
        records = await search_locations(filters=filters, sorts=sorts)
    except ValueError as exc:
        err = f"Invalid search parameter: {exc}"
        log_job("locations", "find", "error", err)
        return {"status": "error", "message": err, "data": []}
    except Exception as exc:  # noqa: BLE001
        err = "Unable to search locations"
        log_job("locations", "find", "error", f"{err}: {exc}")
        return {"status": "error", "message": err, "data": []}

    duration_ms = int((time.perf_counter() - search_started) * 1000)
    message = f"Found {len(records)} locations in {duration_ms} ms"
    log_job("locations", "find", "success", f"{message}; params={filters}, sort={sorts}")

    return {"status": "success", "message": message, "data": records}


@router.post("/validate_links")
async def validate_links_endpoint() -> Dict[str, Any]:
    productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    if not productions_db_id:
        err = "Missing productions master database id"
        log_job("matching", "validate_links", "error", err)
        return {"status": "error", "message": err}

    try:
        prod_locations = await load_all_production_locations(productions_db_id)
        master_cache = await get_locations_master_cached(refresh=True)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load data: {exc}"
        log_job("matching", "validate_links", "error", err)
        return {"status": "error", "message": err}

    result = validate_links(prod_locations, master_cache)
    log_job(
        "matching",
        "validate_links",
        "success",
        f"reviewed={result.get('reviewed')} invalid={result.get('invalid')}",
    )
    return result


@router.post("/match_all")
async def match_all_locations(force: bool = False, refresh: bool = Query(False)) -> Dict[str, Any]:
    start = time.perf_counter()
    try:
        master_cache = await get_locations_master_cached(refresh=True)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load locations cache: {exc}"
        log_job("matching", "match_all", "error", err)
        return {"status": "error", "message": err}

    productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    if not productions_db_id:
        err = "Missing productions master database id"
        log_job("matching", "match_all", "error", err)
        return {"status": "error", "message": err}

    try:
        prod_locations = await load_all_production_locations(productions_db_id, refresh=refresh)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load production locations: {exc}"
        log_job("matching", "match_all", "error", err)
        return {"status": "error", "message": err}

    reviewed = 0
    matched = 0
    conflicts = 0
    unresolved = 0
    match_noop = 0
    total = len(prod_locations)

    for record in prod_locations:
        reviewed += 1
        if not force and record.get("locations_master_ids"):
            continue  # already linked

        match_result = match_to_master(record, master_cache, force=force)
        candidate_count = match_result.get("candidate_count", 0)
        matched_id = match_result.get("matched_master_id")
        if candidate_count > 1:
            conflicts += 1
            log_job(
                "matching",
                "multiple_candidates",
                "success",
                f"record_id={record.get('id')} reason={match_result.get('match_reason')} count={candidate_count}",
            )
            continue

        if not matched_id:
            unresolved += 1
            continue

        if reviewed == 1 or reviewed % 20 == 0:
            pct = round((reviewed / total) * 100) if total else 0
            print(f"[match_all] {reviewed}/{total} ({pct}%)…")

        existing_ids = record.get("locations_master_ids") or []
        existing_master_id = existing_ids[0] if existing_ids else None
        existing_status = record.get("status")
        new_status_name = resolve_status(record.get("place_id"), matched=True, explicit=match_result.get("status"))

        if existing_master_id == matched_id and existing_status == new_status_name:
            log_job(
                "matching",
                "match_noop",
                "success",
                f"record_id={record.get('id')} master_id={matched_id} reason={match_result.get('match_reason')}",
            )
            match_noop += 1
            continue

        props = {
            "LocationsMasterID": {"relation": [{"id": matched_id}]},
            "Status": {"status": {"name": new_status_name}},
        }
        try:
            await update_location_page(record.get("id") or "", props)
            matched += 1
            if force and record.get("locations_master_ids") and record.get("locations_master_ids")[0] != matched_id:
                log_job("matching", "force_rematch_applied", "success", f"record_id={record.get('id')} new_match={matched_id}")
            log_job(
                "matching",
                "matched",
                "success",
                f"record_id={record.get('id')} matched_id={matched_id} reason={match_result.get('match_reason')}",
            )
        except Exception as exc:  # noqa: BLE001
            conflicts += 1
            log_job("matching", "match_update_failed", "error", f"record_id={record.get('id')} error={exc}")

    duration = time.perf_counter() - start
    avg_ms = (duration / reviewed * 1000) if reviewed else 0

    return {
        "status": "success",
        "reviewed": reviewed,
        "matched": matched,
        "conflicts": conflicts,
        "unresolved": unresolved,
        "match_noop": match_noop,
        "duration_ms": round(duration * 1000),
        "avg_per_record_ms": round(avg_ms),
    }
