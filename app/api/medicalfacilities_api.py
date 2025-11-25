from __future__ import annotations

import asyncio
import math
import sys
import time
from typing import Any, Dict, List

from fastapi import APIRouter

from app.services.cache_utils import DEFAULT_MAX_AGE_SECONDS, is_cache_stale
from app.services.logger import log_job
from app.services.notion_medical_facilities import (
    fetch_all_medical_facilities,
    fetch_and_cache_medical_facilities,
    get_cached_medical_facilities,
)
from scripts import fetch_medical_facilities as run_fetch_medical_facilities

router = APIRouter(prefix="/api/medicalfacilities", tags=["medical facilities"])


async def _load_facilities(max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS) -> tuple[List[Dict[str, Any]], str]:
    cache = await get_cached_medical_facilities(max_age_seconds=max_age_seconds)
    normalized = cache.get("normalized") if isinstance(cache, dict) else None
    if isinstance(normalized, list) and not is_cache_stale(cache, max_age_seconds=max_age_seconds):
        return normalized, "cache"

    log_job("facilities", "cache_refresh", "start", "operation=facilities_cache_refresh reason=stale_or_missing")
    facilities = await fetch_and_cache_medical_facilities()
    return facilities, "refreshed"


def _apply_filters(records: List[Dict[str, Any]], filters: Dict[str, str], sort: str | None) -> List[Dict[str, Any]]:
    name_term = (filters.get("name_contains") or "").strip().lower()
    address_term = (filters.get("address_contains") or "").strip().lower()
    state_term = (filters.get("state") or "").strip().upper()
    facility_type = (filters.get("facility_type") or "").strip()

    valid_sorts = {"", "name_asc", "name_desc", "type", "state"}
    if sort and sort not in valid_sorts:
        raise ValueError(f"Unsupported sort value: {sort}")

    filtered: List[Dict[str, Any]] = []
    for row in records:
        name_val = (row.get("name") or "").lower()
        addr_val = (row.get("address") or "").lower()
        state_val = (row.get("state") or "").upper()
        type_val = (row.get("facility_type") or "").strip()

        if name_term and name_term not in name_val:
            continue
        if address_term and address_term not in addr_val:
            continue
        if state_term and (not state_val or state_val != state_term):
            continue
        if facility_type and type_val != facility_type:
            continue
        filtered.append(row)

    sort_key = sort or ""
    if sort_key == "name_asc":
        filtered.sort(key=lambda x: (x.get("name") or "").lower())
    elif sort_key == "name_desc":
        filtered.sort(key=lambda x: (x.get("name") or "").lower(), reverse=True)
    elif sort_key == "type":
        filtered.sort(key=lambda x: (x.get("facility_type") or "").lower())
    elif sort_key == "state":
        filtered.sort(key=lambda x: (x.get("state") or "").upper())

    return filtered


@router.get("/list")
async def list_medical_facilities(page: int = 1, limit: int = 25) -> Dict[str, Any]:
    page = max(1, page)
    limit = min(100, max(1, limit))

    try:
        facilities, source = await _load_facilities()
    except Exception as exc:  # noqa: BLE001
        err = f"Unable to load medical facilities: {exc}"
        log_job("facilities", "list", "error", err)
        return {"status": "error", "message": err}

    total = len(facilities)
    total_pages = max(1, math.ceil(total / limit)) if total else 1
    start = (page - 1) * limit
    end = start + limit
    sliced = facilities[start:end]

    message = f"Returned page {page} of {total_pages} ({total} total) source={source}"
    log_job("facilities", "list", "success", message)
    return {
        "status": "success",
        "message": message,
        "data": {
            "items": sliced,
            "total": total,
            "page": page,
            "limit": limit,
        },
    }


def _run_facility_job() -> dict:
    original_argv = sys.argv[:]  # avoid argparse consuming uvicorn arguments
    sys.argv = ["fetch_medical_facilities"]
    try:
        result = run_fetch_medical_facilities()
        message = str(result)
        log_job(category="facilities", action="fill", status="success", message=message)
        return {"status": "success", "message": message}
    except BaseException as exc:  # noqa: BLE001
        err = f"{exc}"
        log_job(category="facilities", action="fill", status="error", message=err)
        return {"status": "error", "message": err}
    finally:
        sys.argv = original_argv


@router.post("/fill")
async def fill_facilities() -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _run_facility_job)
    return result


@router.get("/find")
async def find_medical_facilities(
    name_contains: str | None = None,
    address_contains: str | None = None,
    state: str | None = None,
    facility_type: str | None = None,
    sort: str | None = None,
) -> Dict[str, Any]:
    filters = {
        "name_contains": name_contains or "",
        "address_contains": address_contains or "",
        "state": state or "",
        "facility_type": facility_type or "",
    }
    sorts = [sort] if sort else []

    search_started = time.perf_counter()
    log_job("facilities", "find", "start", f"Medical facilities search params={filters}, sort={sorts}")

    try:
        facilities, source = await _load_facilities()
        records = _apply_filters(facilities, filters, sort if sort else None)
    except ValueError as exc:
        err = f"Invalid search parameter: {exc}"
        log_job("facilities", "find", "error", err)
        return {"status": "error", "message": err, "data": []}
    except Exception as exc:  # noqa: BLE001
        err = "Unable to search medical facilities"
        log_job("facilities", "find", "error", f"{err}: {exc}")
        return {"status": "error", "message": err, "data": []}

    duration_ms = int((time.perf_counter() - search_started) * 1000)
    message = f"Found {len(records)} facilities in {duration_ms} ms source={source}"
    log_job("facilities", "find", "success", f"{message}; params={filters}, sort={sorts}")

    return {"status": "success", "message": message, "data": records}


def _validate_limit(limit: int, default: int = 1000, max_limit: int = 10_000) -> int:
    if limit is None:
        return default
    if limit < 1 or limit > max_limit:
        raise ValueError(f"limit must be between 1 and {max_limit}")
    return limit


@router.get("/all")
async def all_medical_facilities(limit: int = 1000) -> Dict[str, Any]:
    try:
        validated_limit = _validate_limit(limit)
    except ValueError as exc:
        err = f"Invalid limit: {exc}"
        log_job("facilities", "all", "error", err)
        return {"status": "error", "message": err, "data": []}

    started = time.perf_counter()
    log_job("facilities", "all", "start", f"operation=facilities_bulk_retrieval limit={validated_limit}")

    try:
        records = await fetch_all_medical_facilities(limit=validated_limit)
    except Exception as exc:  # noqa: BLE001
        err = f"Unable to load medical facilities: {exc}"
        log_job("facilities", "all", "error", f"{err}; limit={validated_limit}")
        return {"status": "error", "message": err, "data": []}

    duration_ms = int((time.perf_counter() - started) * 1000)
    message = f"Returned {len(records)} facilities in {duration_ms} ms (limit {validated_limit})"
    log_job("facilities", "all", "success", message)
    return {"status": "success", "message": message, "data": records}
