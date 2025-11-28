import time
from typing import Any, Dict, List

from fastapi import APIRouter, Body, Query

from app.services.address_normalizer import TARGET_FIELDS, apply_master_normalization, normalize_master_rows
from app.services.cache_utils import DEFAULT_MAX_AGE_SECONDS, is_cache_stale
from app.services.dedup_resolve_service import build_merge_plan, choose_primary_with_heuristics
from app.services.dedup_service import find_master_duplicates
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
from app.services.notion_writeback import archive_master_rows, update_master_fields, update_production_master_links, write_address_updates
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


@router.get("/master/dedup")
async def dedup_master_locations(refresh: bool = Query(False)) -> Dict[str, Any]:
    start = time.perf_counter()
    log_job("dedup", "master_dedup", "start", f"refresh={refresh}")
    try:
        master_rows = await get_locations_master_cached(refresh=refresh)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load master locations: {exc}"
        log_job("dedup", "master_dedup", "error", err)
        return {"status": "error", "message": err, "total_master": 0, "duplicate_groups": [], "group_count": 0}

    duplicates = find_master_duplicates(master_rows)
    group_count = len(duplicates)
    total_master = len(master_rows)
    sizes = [len(group.get("rows", [])) for group in duplicates]
    reasons = [group.get("reason") for group in duplicates]
    duration_ms = int((time.perf_counter() - start) * 1000)

    for group in duplicates:
        log_job(
            "dedup",
            "group",
            "success",
            f"group_id={group.get('group_id')} reason={group.get('reason')} size={len(group.get('rows', []))}",
        )

    log_job(
        "dedup",
        "master_dedup",
        "success",
        f"total_master={total_master} groups={group_count} sizes={sizes} reasons={reasons} duration_ms={duration_ms}",
    )

    return {
        "status": "success",
        "message": f"Found {group_count} duplicate groups",
        "total_master": total_master,
        "duplicate_groups": duplicates,
        "group_count": group_count,
    }


@router.get("/master/normalize_preview")
async def normalize_master_preview(refresh: bool = Query(False)) -> Dict[str, Any]:
    start = time.perf_counter()
    log_job("address_normalization", "normalize_preview", "start", f"refresh={refresh}")
    log_job("address_normalization_debug", "preview_call", "success", "normalize_preview using apply_master_normalization(strict=True)")
    try:
        master_rows = await get_locations_master_cached(refresh=refresh)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load master locations: {exc}"
        log_job("address_normalization", "normalize_preview", "error", err)
        return {"status": "error", "message": err, "total_rows": 0, "updated_rows": 0, "sample": []}

    plan = apply_master_normalization(master_rows, strict=True)
    updates = plan.get("updates", [])
    sample: List[Dict[str, Any]] = []
    updated_rows = len(updates)

    for item in updates[:10]:
        row_id = item.get("row_id")
        fields = item.get("fields") or {}
        before = next((r for r in master_rows if (r.get("id") or r.get("row_id")) == row_id), {})
        after = dict(before)
        after.update(fields)
        sample.append(
            {
                "row_id": row_id,
                "filled_fields": list(fields.keys()),
                "before": {k: before.get(k) for k in ["address", "Full Address"] + TARGET_FIELDS},
                "after": {k: after.get(k) for k in ["address", "Full Address"] + TARGET_FIELDS},
            }
        )

    duration_ms = int((time.perf_counter() - start) * 1000)
    log_job(
        "address_normalization",
        "normalize_preview",
        "success",
        f"rows_scanned={plan.get('total_rows', 0)} rows_needing_update={updated_rows} duration_ms={duration_ms}",
    )

    return {
        "status": "success",
        "message": f"Scanned {plan.get('total_rows', 0)} rows; {updated_rows} need structured fields",
        "total_rows": plan.get("total_rows", 0),
        "updated_rows": updated_rows,
        "sample": sample,
    }


@router.get("/master/dedup_resolve_preview")
async def dedup_resolve_preview(group_id: str, refresh: bool = Query(False)) -> Dict[str, Any]:
    start = time.perf_counter()
    log_job("dedup_resolve", "preview", "start", f"group_id={group_id} refresh={refresh}")
    try:
        master_rows = await get_locations_master_cached(refresh=refresh)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load master locations: {exc}"
        log_job("dedup_resolve", "preview", "error", err)
        return {"status": "error", "message": err}

    groups = find_master_duplicates(master_rows)
    target_group = next((g for g in groups if g.get("group_id") == group_id), None)
    if not target_group:
        msg = f"group_id {group_id} not found"
        log_job("dedup_resolve", "preview", "error", msg)
        return {"status": "error", "message": msg}

    rows = target_group.get("rows") or []
    if len(rows) < 2:
        msg = f"group_id {group_id} has fewer than 2 rows"
        log_job("dedup_resolve", "preview", "error", msg)
        return {"status": "error", "message": msg}

    try:
        primary_row, dup_rows = choose_primary_with_heuristics(rows)
    except Exception as exc:  # noqa: BLE001
        err = f"Unable to choose primary: {exc}"
        log_job("dedup_resolve", "preview", "error", err)
        return {"status": "error", "message": err}

    productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    if not productions_db_id:
        err = "Missing productions master database id"
        log_job("dedup_resolve", "preview", "error", err)
        return {"status": "error", "message": err}

    try:
        prod_rows = await load_all_production_locations(productions_db_id, refresh=refresh)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load production locations: {exc}"
        log_job("dedup_resolve", "preview", "error", err)
        return {"status": "error", "message": err}

    plan = build_merge_plan(primary_row, dup_rows, prod_rows)
    duration_ms = int((time.perf_counter() - start) * 1000)
    summary = f"{len(rows)} masters merged -> 1; prod pointers={len(plan.get('prod_loc_updates', []))}"
    log_job(
        "dedup_resolve",
        "preview",
        "success",
        f"group_id={group_id} primary={primary_row.get('id') or primary_row.get('row_id')} duplicates={len(dup_rows)} duration_ms={duration_ms}",
    )

    return {
        "status": "success",
        "group_id": group_id,
        "primary_id": primary_row.get("id") or primary_row.get("row_id"),
        "duplicate_ids": [r.get("id") or r.get("row_id") for r in dup_rows],
        "field_updates": plan.get("field_updates"),
        "prod_loc_updates": plan.get("prod_loc_updates"),
        "delete_master_ids": plan.get("delete_master_ids"),
        "summary": summary,
    }


@router.post("/master/normalize_apply")
async def normalize_master_apply(refresh: bool = Query(False), strict: bool = Query(True)) -> Dict[str, Any]:
    start = time.perf_counter()
    log_job("address_writeback", "apply", "start", f"refresh={refresh} strict={strict}")
    try:
        master_rows = await get_locations_master_cached(refresh=refresh)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load master locations: {exc}"
        log_job("address_writeback", "apply", "error", err)
        return {"status": "error", "message": err}

    plan = apply_master_normalization(master_rows, strict=strict)
    updates = plan.get("updates", [])
    if not updates:
        log_job(
            "address_writeback",
            "apply",
            "success",
            f"rows_scanned={plan.get('total_rows', 0)} rows_updated=0",
        )
        return {
            "status": "success",
            "message": "No rows need updates",
            "total_rows": plan.get("total_rows", 0),
            "rows_updated": 0,
            "writeback": {"attempted": 0, "successful": 0, "failed": 0},
            "sample": [],
        }

    write_result = await write_address_updates(updates)
    await get_locations_master_cached(refresh=True)

    sample = []
    for item in updates[:10]:
        sample.append(
            {
                "row_id": item.get("row_id"),
                "fields": item.get("fields"),
            }
        )

    duration_ms = int((time.perf_counter() - start) * 1000)
    log_job(
        "address_writeback",
        "apply",
        "success",
        f"rows_scanned={plan.get('total_rows', 0)} rows_updated={write_result.get('successful', 0)} duration_ms={duration_ms}",
    )

    return {
        "status": "success",
        "message": f"Applied updates to {write_result.get('successful', 0)} rows",
        "total_rows": plan.get("total_rows", 0),
        "rows_updated": write_result.get("successful", 0),
        "writeback": write_result,
        "sample": sample,
    }


@router.post("/master/dedup_resolve_apply")
async def dedup_resolve_apply(
    payload: Dict[str, Any] | None = Body(None),
    group_id: str | None = Query(None),
    primary_id: str | None = Query(None),
    duplicate_ids: str | None = Query(None),
) -> Dict[str, Any]:
    start = time.perf_counter()
    normalized_body: Dict[str, Any] = {}
    if payload:
        normalized_body = {str(k).lower(): v for k, v in payload.items()}
    group = normalized_body.get("group_id") or group_id
    primary = normalized_body.get("primary_id") or primary_id
    dup_ids = normalized_body.get("duplicate_ids") or []
    if isinstance(duplicate_ids, str) and not dup_ids:
        dup_ids = [d.strip() for d in duplicate_ids.split(",") if d.strip()]
    # Normalize dup_ids if provided as single string in body
    if isinstance(dup_ids, str):
        dup_ids = [d.strip() for d in dup_ids.split(",") if d.strip()]
    if not group or not primary or not dup_ids:
        return {"status": "error", "message": "group_id, primary_id, and duplicate_ids are required"}

    log_job("dedup_resolve", "apply", "start", f"group_id={group} primary_id={primary} duplicates={len(dup_ids)}")

    try:
        master_rows = await get_locations_master_cached(refresh=True)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load master locations: {exc}"
        log_job("dedup_resolve", "apply", "error", err)
        return {"status": "error", "message": err}

    master_by_id = {r.get("id") or r.get("row_id"): r for r in master_rows}
    primary_row = master_by_id.get(primary)
    dup_rows = [master_by_id.get(did) for did in dup_ids if master_by_id.get(did)]

    if not primary_row or not dup_rows:
        err = "Invalid primary_id or duplicate_ids"
        log_job("dedup_resolve", "apply", "error", err)
        return {"status": "error", "message": err}

    productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    if not productions_db_id:
        err = "Missing productions master database id"
        log_job("dedup_resolve", "apply", "error", err)
        return {"status": "error", "message": err}

    try:
        prod_rows = await load_all_production_locations(productions_db_id, refresh=True)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load production locations: {exc}"
        log_job("dedup_resolve", "apply", "error", err)
        return {"status": "error", "message": err}

    plan = build_merge_plan(primary_row, dup_rows, prod_rows)

    field_updates = plan.get("field_updates") or {}
    prod_updates = plan.get("prod_loc_updates") or []
    delete_ids = plan.get("delete_master_ids") or []

    if field_updates:
        await update_master_fields(primary_id, field_updates)
        log_job("dedup_resolve", "primary_updated", "success", f"primary_id={primary_id} fields={list(field_updates.keys())}")

    prod_result = await update_production_master_links(prod_updates)
    archive_result = await archive_master_rows(delete_ids)

    await get_locations_master_cached(refresh=True)
    if productions_db_id:
        await load_all_production_locations(productions_db_id, refresh=True)

    duration_ms = int((time.perf_counter() - start) * 1000)
    log_job(
        "dedup_resolve",
        "apply",
        "success",
        f"group_id={group} primary_id={primary} duplicates={len(dup_rows)} prod_updated={prod_result.get('successful', 0)} archive_success={archive_result.get('successful', 0)} duration_ms={duration_ms}",
    )

    return {
        "status": "success",
        "group_id": group,
        "primary_id": primary,
        "duplicate_ids": dup_ids,
        "field_updates": field_updates,
        "prod_loc_updates": prod_updates,
        "delete_master_ids": delete_ids,
        "writeback": {
            "prod_updates": prod_result,
            "archive": archive_result,
        },
        "summary": f"Merged {len(dup_rows)+1} -> 1; prod pointers updated {prod_result.get('successful', 0)}; archived {archive_result.get('successful', 0)}",
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
