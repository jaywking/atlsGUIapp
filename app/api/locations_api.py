import time
import platform
import sys
from typing import Any, Dict, List

from fastapi import APIRouter, Body, Query
from fastapi.responses import StreamingResponse

from app.services.address_normalizer import TARGET_FIELDS, apply_master_normalization, normalize_master_rows, normalize_table
from app.services.cache_utils import DEFAULT_MAX_AGE_SECONDS, is_cache_stale, load_locations_cache, save_locations_cache
from app.services.dedup_resolve_service import build_merge_plan, choose_primary_with_heuristics
from app.services.dedup_service import find_master_duplicates
from app.services.ingestion_normalizer import normalize_components
from app.services.logger import log_job
from app.services.master_cache import load_master_cache
from app.services.matching_service import match_to_master, stream_match_all, stream_reprocess
from app.services.notion_schema_utils import ensure_schema, search_location_databases
from app.services.notion_locations import (
    fetch_all_locations,
    fetch_and_cache_locations,
    get_cached_locations,
    get_locations_master_cached,
    list_production_location_databases,
    fetch_production_locations,
    fetch_master_by_id,
    load_all_production_locations,
    load_locations_master,
    search_locations,
    update_location_page,
    resolve_status,
)
from app.services.notion_medical_facilities import get_cached_medical_facilities, fetch_and_cache_medical_facilities
from app.services.notion_schema_utils import search_location_databases, ensure_schema
from app.services.notion_writeback import archive_master_rows, update_master_fields, update_production_master_links, write_address_updates
from app.services.validation_service import validate_links
from app.services.create_production import notion_url_for_id
from config import Config
from scripts import process_new_locations

print("DEBUG: locations_api imported successfully")

router = APIRouter(prefix="/api/locations", tags=["locations"])
_detail_cache: Dict[str, Dict[str, Any]] = {}
_DETAIL_CACHE_TTL = 60  # seconds


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


def _clean_term(value: str | None) -> str:
    return (value or "").strip()


def _lower_term(value: str | None) -> str:
    return _clean_term(value).lower()


def _contains(haystack: str, needle: str) -> bool:
    if not needle:
        return True
    return needle in (haystack or "").lower()


def _equals(haystack: str, needle: str) -> bool:
    if not needle:
        return True
    return (haystack or "").lower() == needle


def _serialize_master_row(row: Dict[str, Any]) -> Dict[str, Any]:
    types = row.get("types") or []
    place_type = types[0] if isinstance(types, list) and types else ""
    return {
        "row_id": row.get("row_id") or row.get("id") or "",
        "master_id": row.get("prod_loc_id") or "",
        "name": row.get("name") or row.get("location_name") or row.get("practical_name") or "",
        "full_address": row.get("address") or "",
        "city": row.get("city") or "",
        "state": row.get("state") or "",
        "country": row.get("country") or "",
        "place_id": row.get("place_id") or "",
        "status": row.get("status") or "",
        "place_type": place_type,
        "location_op_status": row.get("location_op_status") or "",
        "google_maps_url": row.get("google_maps_url") or "",
    }


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


@router.get("/search_master")
async def search_master_locations(
    production_name: str | None = None,
    location_name: str | None = None,
    full_address: str | None = None,
    city: str | None = None,
    state: str | None = None,
    country: str | None = None,
    zip_code: str | None = None,
    county: str | None = None,
    borough: str | None = None,
    place_type: str | None = None,
    status: str | None = None,
    location_op_status: str | None = None,
    place_id: str | None = None,
    master_id: str | None = None,
    limit: int = 500,
) -> Dict[str, Any]:
    start = time.perf_counter()
    try:
        validated_limit = _validate_limit(limit, default=500, max_limit=5_000)
    except ValueError as exc:
        err = f"Invalid limit: {exc}"
        log_job("locations", "search_master", "error", err)
        return {"status": "error", "message": err, "data": {"items": [], "total": 0, "truncated": False}}

    prod_term = _lower_term(production_name)
    filters = {
        "location_name": _lower_term(location_name),
        "full_address": _lower_term(full_address),
        "city": _lower_term(city),
        "state": _lower_term(state),
        "country": _lower_term(country),
        "zip": _lower_term(zip_code),
        "county": _lower_term(county),
        "borough": _lower_term(borough),
        "place_type": _lower_term(place_type),
        "status": _lower_term(status),
        "location_op_status": _lower_term(location_op_status),
        "place_id": _lower_term(place_id),
        "master_id": _lower_term(master_id),
    }

    log_job(
        "locations",
        "search_master",
        "start",
        f"production_name={prod_term} filters={filters} limit={validated_limit}",
    )

    try:
        master_rows = await get_locations_master_cached(refresh=False)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load Locations Master: {exc}"
        log_job("locations", "search_master", "error", err)
        return {"status": "error", "message": err, "data": {"items": [], "total": 0, "truncated": False}}

    master_by_id = {r.get("row_id") or r.get("id"): r for r in master_rows}

    results: List[Dict[str, Any]] = []

    if prod_term:
        productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
        if not productions_db_id:
            err = "Missing productions master database id"
            log_job("locations", "search_master", "error", err)
            return {"status": "error", "message": err, "data": {"items": [], "total": 0, "truncated": False}}

        try:
            prod_entries = await list_production_location_databases(productions_db_id)
        except Exception as exc:  # noqa: BLE001
            err = f"Failed to list production databases: {exc}"
            log_job("locations", "search_master", "error", err)
            return {"status": "error", "message": err, "data": {"items": [], "total": 0, "truncated": False}}

        matched_entries = []
        for entry in prod_entries:
            hay = " ".join(
                [
                    entry.get("display_name") or "",
                    entry.get("production_title") or "",
                    entry.get("production_id") or "",
                    entry.get("db_title") or "",
                ]
            ).lower()
            if prod_term in hay:
                matched_entries.append(entry)

        if not matched_entries:
            duration_ms = int((time.perf_counter() - start) * 1000)
            message = f"No productions matched '{production_name}'"
            log_job("locations", "search_master", "success", f"{message} duration_ms={duration_ms}")
            return {"status": "success", "message": message, "data": {"items": [], "total": 0, "truncated": False}}

        seen_ids: set[str] = set()
        for entry in matched_entries:
            db_id = entry.get("locations_db_id") or ""
            if not db_id:
                continue
            prod_rows = await fetch_production_locations(db_id, production_id=entry.get("production_id"))
            for row in prod_rows:
                for master_id_rel in row.get("locations_master_ids") or []:
                    if master_id_rel in seen_ids:
                        continue
                    master_row = master_by_id.get(master_id_rel)
                    if not master_row:
                        continue
                    seen_ids.add(master_id_rel)
                    if len(results) < validated_limit:
                        results.append(_serialize_master_row(master_row))

        total_found = len(seen_ids)
        truncated = total_found > len(results)
    else:
        for row in master_rows:
            name_val = (row.get("name") or row.get("location_name") or row.get("practical_name") or "").lower()
            full_addr_val = (row.get("address") or "").lower()
            city_val = (row.get("city") or "").lower()
            state_val = (row.get("state") or "").lower()
            country_val = (row.get("country") or "").lower()
            zip_val = (row.get("zip") or "").lower()
            county_val = (row.get("county") or "").lower()
            borough_val = (row.get("borough") or "").lower()
            status_val = (row.get("status") or "").lower()
            op_status_val = (row.get("location_op_status") or "").lower()
            place_val = (row.get("place_id") or "").lower()
            master_val = (row.get("prod_loc_id") or "").lower()
            types_val = row.get("types") or []
            types_lower = [
                t.lower() for t in types_val if isinstance(t, str)
            ] if isinstance(types_val, list) else []

            if not _contains(name_val, filters["location_name"]):
                continue
            if not _contains(full_addr_val, filters["full_address"]):
                continue
            if not _contains(city_val, filters["city"]):
                continue
            if not _contains(state_val, filters["state"]):
                continue
            if not _equals(country_val, filters["country"]):
                continue
            if not _contains(zip_val, filters["zip"]):
                continue
            if not _contains(county_val, filters["county"]):
                continue
            if not _contains(borough_val, filters["borough"]):
                continue
            if filters["status"] and not _equals(status_val, filters["status"]):
                continue
            if filters["location_op_status"] and not _equals(op_status_val, filters["location_op_status"]):
                continue
            if filters["place_id"] and not _equals(place_val, filters["place_id"]):
                continue
            if filters["master_id"] and not _equals(master_val, filters["master_id"]):
                continue
            if filters["place_type"]:
                requested_types = [t.strip() for t in filters["place_type"].split(",") if t.strip()]
                if requested_types and not any(rt in types_lower for rt in requested_types):
                    continue

            results.append(_serialize_master_row(row))
            if len(results) >= validated_limit:
                break

        total_found = len(results)
        truncated = False

    results.sort(key=lambda r: (r.get("master_id") or "").lower())
    duration_ms = int((time.perf_counter() - start) * 1000)
    message = f"Returned {len(results)} Locations Master rows in {duration_ms} ms"
    log_job(
        "locations",
        "search_master",
        "success",
        f"{message} total={total_found} truncated={truncated} production={bool(prod_term)}",
    )
    return {
        "status": "success",
        "message": message,
        "data": {"items": results, "total": total_found, "truncated": truncated},
    }


@router.get("/detail")
async def get_location_detail(master_id: str | None = None) -> Dict[str, Any]:
    master_id = (master_id or "").strip()
    if not master_id:
        return {"status": "error", "message": "master_id is required", "data": {}}

    cached = _detail_cache.get(master_id)
    if cached and (time.time() - cached.get("ts", 0)) < _DETAIL_CACHE_TTL:
        return cached.get("payload", {})

    try:
        master_row = await fetch_master_by_id(master_id)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load Locations Master: {exc}"
        log_job("locations", "detail", "error", err)
        return {"status": "error", "message": err, "data": {}}
    if not master_row:
        return {"status": "error", "message": f"Location {master_id} not found", "data": {}}

    productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    productions: List[Dict[str, str]] = []
    if productions_db_id:
        try:
            prod_entries = await list_production_location_databases(productions_db_id)
            master_page_id = master_row.get("row_id") or master_row.get("id") or ""
            seen_productions: set[str] = set()
            for entry in prod_entries:
                db_id = entry.get("locations_db_id") or ""
                if not db_id:
                    continue
                prod_rows = await fetch_production_locations(db_id, production_id=entry.get("production_id"))
                if not master_page_id:
                    continue
                linked = any(master_page_id in (row.get("locations_master_ids") or []) for row in prod_rows)
                if not linked:
                    continue
                prod_name = entry.get("display_name") or entry.get("production_title") or entry.get("production_id") or "Production"
                prod_id = entry.get("production_id") or prod_name
                if prod_id in seen_productions:
                    continue
                seen_productions.add(prod_id)
                productions.append({"production_name": prod_name, "production_id": prod_id})
        except Exception as exc:  # noqa: BLE001
            log_job("locations", "detail", "error", f"production_usage_failed: {exc}")

    facilities: Dict[str, Any] = {"er": None, "ucs": []}
    try:
        facilities_cache = await get_cached_medical_facilities()
        normalized = facilities_cache.get("normalized") if isinstance(facilities_cache, dict) else None
        if not isinstance(normalized, list) or not normalized:
            normalized = await fetch_and_cache_medical_facilities()
        facility_by_id = {f.get("row_id") or f.get("id"): f for f in normalized if f.get("row_id") or f.get("id")}

        er_ids = master_row.get("er_ids") or []
        uc_ids: List[str] = []
        for key in ("uc1_ids", "uc2_ids", "uc3_ids"):
            uc_ids.extend(master_row.get(key) or [])

        er_id = er_ids[0] if er_ids else ""
        if er_id:
            er = facility_by_id.get(er_id)
            if er:
                facilities["er"] = {
                    "name": er.get("name") or "",
                    "facility_type": er.get("facility_type") or "",
                    "address": er.get("address") or "",
                    "phone": er.get("phone") or "",
                    "google_maps_url": er.get("google_maps_url") or "",
                    "notion_url": er.get("notion_url") or "",
                }

        for uc_id in uc_ids[:2]:
            facility = facility_by_id.get(uc_id)
            if not facility:
                continue
            facilities["ucs"].append(
                {
                    "name": facility.get("name") or "",
                    "facility_type": facility.get("facility_type") or "",
                    "address": facility.get("address") or "",
                    "phone": facility.get("phone") or "",
                    "google_maps_url": facility.get("google_maps_url") or "",
                    "notion_url": facility.get("notion_url") or "",
                }
            )
    except Exception as exc:  # noqa: BLE001
        log_job("locations", "detail", "error", f"facilities_lookup_failed: {exc}")

    types = master_row.get("types") or []
    detail = {
        "master_id": master_id,
        "name": master_row.get("name") or "",
        "practical_name": master_row.get("practical_name") or "",
        "location_name": master_row.get("location_name") or "",
        "full_address": master_row.get("address") or "",
        "address1": master_row.get("address1") or "",
        "address2": master_row.get("address2") or "",
        "address3": master_row.get("address3") or "",
        "city": master_row.get("city") or "",
        "state": master_row.get("state") or "",
        "zip": master_row.get("zip") or "",
        "country": master_row.get("country") or "",
        "county": master_row.get("county") or "",
        "borough": master_row.get("borough") or "",
        "latitude": master_row.get("latitude"),
        "longitude": master_row.get("longitude"),
        "place_id": master_row.get("place_id") or "",
        "place_types": types if isinstance(types, list) else [],
        "status": master_row.get("status") or "",
        "location_op_status": master_row.get("location_op_status") or "",
        "google_maps_url": master_row.get("google_maps_url") or "",
        "formatted_address_google": master_row.get("formatted_address_google") or "",
        "created_time": master_row.get("created_time") or "",
        "updated_time": master_row.get("updated_time") or "",
        "notion_page_id": master_row.get("row_id") or master_row.get("id") or "",
    }
    if detail["notion_page_id"]:
        detail["notion_url"] = notion_url_for_id(detail["notion_page_id"])
    else:
        detail["notion_url"] = ""

    payload = {
        "status": "success",
        "message": f"Loaded {master_id}",
        "data": {"location": detail, "productions": productions, "medical_facilities": facilities},
    }
    _detail_cache[master_id] = {"ts": time.time(), "payload": payload}
    return payload


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


@router.post("/normalize/preview")
async def normalize_any_table_preview(payload: Dict[str, Any]) -> Dict[str, Any]:
    table = str(payload.get("table") or "").strip()
    if not table:
        return {"status": "error", "message": "table is required"}
    try:
        result = await normalize_table(table, preview=True)
        return {"status": result.get("status", "success"), "message": result.get("message", ""), "data": result}
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to preview normalization for {table}: {exc}"
        log_job("address_normalization", "normalize_preview", "error", err)
        return {"status": "error", "message": err}


@router.post("/normalize/apply")
async def normalize_any_table_apply(payload: Dict[str, Any]) -> Dict[str, Any]:
    table = str(payload.get("table") or "").strip()
    if not table:
        return {"status": "error", "message": "table is required"}
    try:
        result = await normalize_table(table, preview=False)
        return {"status": result.get("status", "success"), "message": result.get("message", ""), "data": result}
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to apply normalization for {table}: {exc}"
        log_job("address_normalization", "normalize_apply", "error", err)
        return {"status": "error", "message": err}


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

    field_updates = normalize_components(plan.get("field_updates") or {})
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


@router.get("/match_all_stream")
async def match_all_locations_stream(force: bool = False, refresh: bool = Query(False)) -> StreamingResponse:
    try:
        master_cache = await load_master_cache(refresh=True)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load locations cache: {exc}"
        log_job("matching", "match_all_stream", "error", err)
        return StreamingResponse(iter([f"error: {err}"]), media_type="text/plain")

    productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    if not productions_db_id:
        err = "Missing productions master database id"
        log_job("matching", "match_all_stream", "error", err)
        return StreamingResponse(iter([f"error: {err}"]), media_type="text/plain")

    try:
        prod_locations = await load_all_production_locations(productions_db_id, refresh=refresh)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load production locations: {exc}"
        log_job("matching", "match_all_stream", "error", err)
        return StreamingResponse(iter([f"error: {err}"]), media_type="text/plain")

    async def _generator():
        async for line in stream_match_all(
            prod_locations,
            master_cache,
            resolve_status_fn=resolve_status,
            update_page_fn=update_location_page,
            force=force,
        ):
            yield line + "\n"

    return StreamingResponse(_generator(), media_type="text/plain")


@router.get("/dedup_stream")
async def dedup_stream(refresh: bool = Query(False)) -> StreamingResponse:
    async def _generator():
        groups = 0
        try:
            master_rows = await get_locations_master_cached(refresh=True)
            yield f"Scanning Locations Master ({len(master_rows)} rows)...\n"
            count, msgs = _stream_duplicates("Locations Master", master_rows)
            groups += count
            for line in msgs:
                yield line
            productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
            if productions_db_id:
                prod_entries = await list_production_location_databases(productions_db_id)
                for entry in prod_entries:
                    dbid = entry.get("locations_db_id")
                    name = entry.get("display_name") or entry.get("production_title") or dbid
                    if not dbid:
                        continue
                    try:
                        rows = await fetch_production_locations(dbid, production_id=name)
                    except Exception as exc:  # noqa: BLE001
                        yield f"Scanning {name} ({dbid}) failed: {exc}\n"
                        continue
                    yield f"Scanning Production {name} ({len(rows)} rows)...\n"
                    count, msgs = _stream_duplicates(name, rows)
                    groups += count
                    for line in msgs:
                        yield line
            yield f"Done. groups={groups}\n"
        except Exception as exc:  # noqa: BLE001
            yield f"error: {exc}\n"

    return StreamingResponse(_generator(), media_type="text/plain")


def _stream_duplicates(label: str, rows: List[Dict[str, Any]]) -> tuple[int, List[str]]:
    groups = 0
    messages: List[str] = []
    by_place: Dict[str, List[Dict[str, Any]]] = {}
    by_hash: Dict[tuple, List[Dict[str, Any]]] = {}
    for row in rows:
        pid = (row.get("place_id") or "").strip().lower()
        if pid:
            by_place.setdefault(pid, []).append(row)
        h = (
            (row.get("address1") or "").strip().lower(),
            (row.get("city") or "").strip().lower(),
            (row.get("state") or "").strip().lower(),
            (row.get("zip") or "").strip().lower(),
            (row.get("country") or "").strip().lower(),
        )
        if any(h):
            by_hash.setdefault(h, []).append(row)
    for bucket in [by_place, by_hash]:
        for dup_rows in bucket.values():
            if len(dup_rows) > 1:
                groups += 1
                messages.append(f"-> Duplicate Group ({label}) count={len(dup_rows)}\n")
    return groups, messages


@router.get("/diagnostics_stream")
async def diagnostics_stream(refresh: bool = Query(False)) -> StreamingResponse:
    async def _generator():
        try:
            master = await get_locations_master_cached(refresh=True)
            yield f"Diagnostics:\nMaster: {len(master)} rows\n"
            missing_pid = sum(1 for r in master if not r.get("place_id"))
            yield f"-> missing_place_id={missing_pid}\n"
            productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
            if productions_db_id:
                prod_entries = await list_production_location_databases(productions_db_id)
                for entry in prod_entries:
                    dbid = entry.get("locations_db_id")
                    name = entry.get("display_name") or entry.get("production_title") or dbid
                    if not dbid:
                        continue
                    try:
                        rows = await fetch_production_locations(dbid, production_id=name)
                        missing_full = sum(1 for r in rows if not r.get("address"))
                        missing_pid_prod = sum(1 for r in rows if not r.get("place_id"))
                        yield f"{name} ({len(rows)} rows): missing_full_address={missing_full} missing_place_id={missing_pid_prod}\n"
                    except Exception as exc:  # noqa: BLE001
                        yield f"{name}: error {exc}\n"
            cache = await load_master_cache(refresh=True)
            place_size = len(cache.get("place_id_index", {}))
            hash_size = len(cache.get("canonical_hash_index", {}))
            yield f"Cache: place_id_index={place_size} hash_index={hash_size}\n"
            notion_status = "loaded" if Config.NOTION_TOKEN else "missing"
            maps_status = "loaded" if Config.GOOGLE_MAPS_API_KEY else "missing"
            yield f"APIs: Notion={notion_status} GoogleMaps={maps_status}\n"
            yield "Done.\n"
        except Exception as exc:  # noqa: BLE001
            yield f"error: {exc}\n"

    return StreamingResponse(_generator(), media_type="text/plain")


@router.get("/system_info")
async def system_info() -> Dict[str, Any]:
    master_cache = await load_master_cache(refresh=True)
    cache_info = {
        "master_rows": len(master_cache.get("rows", [])),
        "place_id_index": len(master_cache.get("place_id_index", {})),
        "hash_index": len(master_cache.get("canonical_hash_index", {})),
    }
    return {
        "status": "success",
        "data": {
            "application": {
                "version": "v0.9.4",
                "python": sys.version.split()[0],
                "platform": platform.platform(),
            },
            "dependencies": {},
            "cache": cache_info,
            "credentials": {
                "notion_token": bool(Config.NOTION_TOKEN),
                "google_maps_api_key": bool(Config.GOOGLE_MAPS_API_KEY),
            },
        },
    }


@router.get("/status")
async def status() -> Dict[str, str]:
    return {"status": "ok"}


@router.get("/schema_update_stream")
async def schema_update_stream() -> StreamingResponse:
    # Build list of DBs: configured master/facilities + discovered _Locations
    db_ids: List[str] = []
    db_names: Dict[str, str] = {}
    for db_id in filter(None, [Config.LOCATIONS_MASTER_DB, Config.MEDICAL_FACILITIES_DB]):
        db_ids.append(db_id)
        db_names[db_id] = db_id
    try:
        discovered = await search_location_databases()
        for item in discovered:
            db_id = item.get("id")
            if db_id and db_id not in db_ids:
                db_ids.append(db_id)
                title_blocks = item.get("title") or []
                title_text = "".join([t.get("plain_text", "") for t in title_blocks if isinstance(t, dict)]).strip()
                db_names[db_id] = title_text or db_id
    except Exception as exc:  # noqa: BLE001
        log_job("schema_update_stream", "discover", "error", f"discover_failed: {exc}")

    total = len(db_ids)

    async def _generator():
        updated = skipped = failed = 0
        for idx, db_id in enumerate(db_ids, start=1):
            name = db_names.get(db_id, db_id)
            yield f"Checking {idx}/{total}: {name}...\n"
            try:
                changed, fields = await ensure_schema(db_id)
                if changed:
                    updated += 1
                    yield f"-> patched {len(fields)} fields\n"
                else:
                    skipped += 1
                    yield "-> no changes\n"
            except Exception as exc:  # noqa: BLE001
                failed += 1
                yield f"-> FAILED: {exc}\n"
        yield f"Done. updated={updated} skipped={skipped} failed={failed}\n"

    return StreamingResponse(_generator(), media_type="text/plain")


@router.get("/cache_refresh_stream")
async def cache_refresh_stream() -> StreamingResponse:
    async def _generator():
        try:
            yield "Starting cache refresh...\n"
            locations = await fetch_and_cache_locations()
            total = len(locations)
            yield f"Refreshed locations cache: {total} rows\n"
            yield "Done.\n"
        except Exception as exc:  # noqa: BLE001
            yield f"Failed: {exc}\n"

    return StreamingResponse(_generator(), media_type="text/plain")


@router.get("/cache_purge_stream")
async def cache_purge_stream() -> StreamingResponse:
    async def _generator():
        try:
            yield "Purging dedup cache...\n"
            # No dedicated dedup cache implemented; placeholder message.
            yield "No dedicated dedup cache configured; nothing to purge.\n"
            yield "Done.\n"
        except Exception as exc:  # noqa: BLE001
            yield f"Failed: {exc}\n"

    return StreamingResponse(_generator(), media_type="text/plain")


@router.get("/cache_reload_stream")
async def cache_reload_stream() -> StreamingResponse:
    async def _generator():
        try:
            yield "Reloading all places data...\n"
            master_cache = await load_master_cache(refresh=True)
            rows = master_cache.get("rows", [])
            yield f"Loaded {len(rows)} master rows\n"
            yield "Rebuilding locations cache...\n"
            locations = await fetch_and_cache_locations()
            yield f"Rebuilt locations cache with {len(locations)} rows\n"
            yield "Done.\n"
        except Exception as exc:  # noqa: BLE001
            yield f"Failed: {exc}\n"

    return StreamingResponse(_generator(), media_type="text/plain")


@router.get("/production_dbs")
async def list_production_dbs() -> Dict[str, Any]:
    productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    if not productions_db_id:
        return {"status": "error", "message": "Missing productions master database id", "data": []}
    try:
        entries_raw = await list_production_location_databases(productions_db_id)
        entries: List[Dict[str, Any]] = []
        for entry in entries_raw:
            production_title = entry.get("production_title") or entry.get("production_id") or ""
            db_title = entry.get("db_title") or ""
            db_id = entry.get("locations_db_id") or ""
            display_name = entry.get("display_name") or production_title or db_title or entry.get("abbreviation") or "Production"
            if display_name == db_id or not display_name.strip():
                display_name = production_title or "Production"
            entries.append(
                {
                    "display_name": display_name,
                    "production_title": production_title,
                    "production_id": entry.get("production_id") or "",
                    "locations_db_id": db_id,
                }
            )
        return {"status": "success", "data": entries}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": str(exc), "data": []}


@router.get("/reprocess_stream")
async def reprocess_stream(force: bool = False, db_id: str | None = Query(None)) -> StreamingResponse:
    productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    if not productions_db_id:
        return StreamingResponse(iter(["error: Missing productions master database id\n"]), media_type="text/plain")

    try:
        prod_entries = await list_production_location_databases(productions_db_id)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to list production databases: {exc}"
        return StreamingResponse(iter([f"error: {err}\n"]), media_type="text/plain")

    target_db = (db_id or "").strip()
    if target_db:
        filtered = [entry for entry in prod_entries if (entry.get("locations_db_id") or "").strip() == target_db]
        if not filtered:
            return StreamingResponse(iter([f"Error: Production database {target_db} not found. Aborting.\n"]), media_type="text/plain")
        prod_entries = filtered

    async def _generator():
        if target_db and not prod_entries:
            yield f"Error: Production database {target_db} not found. Aborting.\n"
            return
        if target_db:
            yield f"Selected Production: {(prod_entries[0].get('display_name') or 'Production')} ({target_db})\n"
        else:
            yield "Reprocessing all productions...\n"

        try:
            master_cache = await load_master_cache(refresh=True)
        except Exception as exc:  # noqa: BLE001
            yield f"error: Failed to load master cache: {exc}\n"
            return

        total_rows = updated = skipped = unmatched = errors = 0
        summaries: List[str] = []
        productions_processed = 0

        for entry in prod_entries:
            prod_name = entry.get("display_name") or entry.get("production_title") or entry.get("production_id") or entry.get("name") or entry.get("locations_db_id") or "Production"
            current_db_id = entry.get("locations_db_id")
            if not current_db_id:
                continue
            productions_processed += 1
            if not target_db:
                yield f"Production: {prod_name} ({current_db_id})\n"
            try:
                rows = await fetch_production_locations(current_db_id, production_id=prod_name)
            except Exception as exc:  # noqa: BLE001
                errors += 1
                yield f"-> error loading rows: {exc}\n"
                continue
            count = len(rows)
            total_rows += count
            yield f"Rows: {count}\n"
            prod_updated = prod_skipped = prod_unmatched = prod_errors = 0
            for idx, row in enumerate(rows, start=1):
                yield f"Row {idx}/{count} - "
                try:
                    from app.services.ingestion_normalizer import normalize_ingest_record

                    normalized_row = normalize_ingest_record(row, production_id=prod_name, log_category="reprocess", log=False)
                    match_result = match_to_master(
                        {
                            "id": row.get("id"),
                            "address1": normalized_row["components"].get("address1"),
                            "city": normalized_row["components"].get("city"),
                            "state": normalized_row["components"].get("state"),
                            "zip": normalized_row["components"].get("zip"),
                            "country": normalized_row["components"].get("country"),
                            "place_id": normalized_row.get("place_id"),
                        },
                        master_cache,
                        force=force,
                    )
                    match_reason = match_result.get("match_reason") or "none"
                    candidate_count = match_result.get("candidate_count", 0)
                    matched_id = match_result.get("matched_master_id")
                    if candidate_count > 1:
                        prod_unmatched += 1
                        unmatched += 1
                        yield f"multiple candidates via {match_reason}\n"
                        continue
                    if not matched_id:
                        prod_unmatched += 1
                        unmatched += 1
                        yield "no match found\n"
                        continue

                    props = {
                        "address1": {"rich_text": [{"text": {"content": normalized_row["components"].get("address1") or ""}}]},
                        "address2": {"rich_text": [{"text": {"content": normalized_row["components"].get("address2") or ""}}]},
                        "address3": {"rich_text": [{"text": {"content": normalized_row["components"].get("address3") or ""}}]},
                        "city": {"rich_text": [{"text": {"content": normalized_row["components"].get("city") or ""}}]},
                        "state": {"rich_text": [{"text": {"content": normalized_row["components"].get("state") or ""}}]},
                        "zip": {"rich_text": [{"text": {"content": normalized_row["components"].get("zip") or ""}}]},
                        "country": {"rich_text": [{"text": {"content": normalized_row["components"].get("country") or ""}}]},
                        "county": {"rich_text": [{"text": {"content": normalized_row["components"].get("county") or ""}}]},
                        "borough": {"rich_text": [{"text": {"content": normalized_row["components"].get("borough") or ""}}]},
                        "Full Address": {"rich_text": [{"text": {"content": normalized_row.get("full_address") or ""}}]},
                        "Place_ID": {"rich_text": [{"text": {"content": normalized_row.get("place_id") or ""}}]},
                        "LocationsMasterID": {"relation": [{"id": matched_id}]},
                    }
                    if normalized_row.get("formatted_address_google"):
                        props["formatted_address_google"] = {"rich_text": [{"text": {"content": normalized_row.get("formatted_address_google")}}]}
                    if normalized_row.get("latitude") is not None:
                        props["Latitude"] = {"number": normalized_row.get("latitude")}
                    if normalized_row.get("longitude") is not None:
                        props["Longitude"] = {"number": normalized_row.get("longitude")}

                    def _rt_value(prop: Dict[str, Any]) -> str:
                        parts = prop.get("rich_text") or []
                        if not parts:
                            return ""
                        return parts[0].get("text", {}).get("content", "") or ""

                    def _num_matches(current: Any, expected: Any) -> bool:
                        if current is None and expected is None:
                            return True
                        try:
                            return abs(float(current) - float(expected)) < 1e-6
                        except Exception:
                            return False

                    def _needs_write(current_row: Dict[str, Any], payload: Dict[str, Any]) -> bool:
                        key_map = {
                            "address1": "address1",
                            "address2": "address2",
                            "address3": "address3",
                            "city": "city",
                            "state": "state",
                            "zip": "zip",
                            "country": "country",
                            "county": "county",
                            "borough": "borough",
                            "Full Address": "address",
                            "Place_ID": "place_id",
                            "formatted_address_google": "formatted_address_google",
                        }
                        for key, value in payload.items():
                            if key == "LocationsMasterID":
                                existing_ids = current_row.get("locations_master_ids") or []
                                target_ids = [rel.get("id") for rel in value.get("relation", []) if rel.get("id")]
                                if target_ids and target_ids[0] not in existing_ids:
                                    return True
                                continue
                            if key in {"Latitude", "Longitude"}:
                                current_val = current_row.get("latitude") if key == "Latitude" else current_row.get("longitude")
                                if not _num_matches(current_val, value.get("number")):
                                    return True
                                continue
                            mapped = key_map.get(key)
                            if not mapped:
                                return True
                            expected = _rt_value(value)
                            current_val = current_row.get(mapped) or ""
                            if str(current_val) != str(expected):
                                return True
                        return False

                    if _needs_write(row, props):
                        await update_location_page(row.get("id") or "", props)
                        prod_updated += 1
                        updated += 1
                        yield f"address normalized -> matched to existing record in Locations Master via {match_reason}\n"
                    else:
                        prod_skipped += 1
                        skipped += 1
                        yield "No changes - already matched.\n"
                except Exception as exc:  # noqa: BLE001
                    prod_errors += 1
                    errors += 1
                    yield f"error: {exc}\n"
            summaries.append(
                "Summary for {prod}:\nSkipped={skipped}\nUpdated={updated}\nUnmatched={unmatched}\nErrors={errors}\n".format(
                    prod=prod_name,
                    skipped=prod_skipped,
                    updated=prod_updated,
                    unmatched=prod_unmatched,
                    errors=prod_errors,
                )
            )

        yield "\nDone.\n"
        for summary in summaries:
            yield summary

    return StreamingResponse(_generator(), media_type="text/plain")
