from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from app.services.address_parser import parse_address
from app.services.cache_utils import DEFAULT_MAX_AGE_SECONDS, _utc_now, is_cache_stale, load_facilities_cache, save_facilities_cache
from app.services.logger import log_job
from config import Config

NOTION_VERSION = "2022-06-28"
PAGE_SIZE = 100
DEFAULT_COUNTRY = "US"
CACHE_SCHEMA_VERSION = 3


def _rich_text(props: Dict[str, Any], key: str) -> str:
    arr = props.get(key, {}).get("rich_text", [])
    return " ".join([a.get("plain_text", "") for a in arr if isinstance(a, dict)]) if arr else ""


def _title(props: Dict[str, Any], key: str) -> str:
    arr = props.get(key, {}).get("title", [])
    return " ".join([a.get("plain_text", "") for a in arr if isinstance(a, dict)]) if arr else ""


def _url(props: Dict[str, Any], key: str) -> str:
    return props.get(key, {}).get("url") or ""


def _select(props: Dict[str, Any], key: str) -> str:
    sel = props.get(key, {}).get("select") or {}
    return sel.get("name") or ""


def _number(props: Dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        num = props.get(key, {}).get("number")
        if num is not None:
            return float(num)
    return None


def _phone(props: Dict[str, Any], key: str) -> str:
    return props.get(key, {}).get("phone_number") or ""


def _build_hours(props: Dict[str, Any]) -> str:
    days = [
        ("Monday Hours", "Mon"),
        ("Tuesday Hours", "Tue"),
        ("Wednesday Hours", "Wed"),
        ("Thursday Hours", "Thu"),
        ("Friday Hours", "Fri"),
        ("Saturday Hours", "Sat"),
        ("Sunday Hours", "Sun"),
    ]
    parts = []
    for prop_name, label in days:
        val = _rich_text(props, prop_name)
        if val:
            cleaned = val.strip()
            for day_name in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
                if cleaned.lower().startswith(day_name.lower() + ":"):
                    cleaned = cleaned[len(day_name) + 1 :].strip()
                    break
            parts.append(f"{label}: {cleaned}")
    return "; ".join(parts)


def _safe_country(value: Optional[str]) -> str:
    return (value or DEFAULT_COUNTRY).upper()


def _full_address_from_components(components: Dict[str, Optional[str]]) -> str:
    lines: List[str] = []
    for key in ("address1", "address2", "address3"):
        val = components.get(key)
        if val:
            lines.append(val.strip())
    city = (components.get("city") or "").strip()
    state = (components.get("state") or "").strip()
    postal = (components.get("zip") or "").strip()
    city_line = ""
    if city:
        city_line = city
    if state:
        city_line = f"{city_line}, {state}" if city_line else state
    if postal:
        city_line = f"{city_line} {postal}".strip()
    if city_line:
        lines.append(city_line)
    return "\n".join([line for line in lines if line]).strip()


def normalize_facility(page: Dict[str, Any]) -> Dict[str, Any]:
    props = page.get("properties") or {}
    facility_id = _title(props, "MedicalFacilityID") or _rich_text(props, "MedicalFacilityID")
    name = _rich_text(props, "Name") or facility_id
    facility_type = _select(props, "Type")
    distance_val = _number(props, "Distance", "Distance (mi)")
    phone_val = _phone(props, "Phone") or _phone(props, "International Phone") or _rich_text(props, "Phone") or _rich_text(props, "International Phone")
    state_val = _select(props, "State")
    full_address_raw = _rich_text(props, "Full Address") or _rich_text(props, "Address")
    address1 = _rich_text(props, "address1") or _rich_text(props, "Address 1") or _rich_text(props, "Address1")
    address2 = _rich_text(props, "address2") or _rich_text(props, "Address 2") or _rich_text(props, "Address2")
    address3 = _rich_text(props, "address3") or _rich_text(props, "Address 3") or _rich_text(props, "Address3")
    city = _rich_text(props, "city") or _rich_text(props, "City")
    state_province = _rich_text(props, "state") or _rich_text(props, "State / Province") or state_val
    zip_code = _rich_text(props, "zip") or _rich_text(props, "ZIP / Postal Code") or _rich_text(props, "Postal Code") or _rich_text(props, "ZIP")
    country = _safe_country(_rich_text(props, "country") or _rich_text(props, "Country"))
    county = _rich_text(props, "county") or _rich_text(props, "County")
    borough = _rich_text(props, "borough") or _rich_text(props, "Borough")

    parsed = parse_address(full_address_raw)
    if not state_province and parsed.get("state"):
        state_province = parsed.get("state")
    if not zip_code and parsed.get("zip"):
        zip_code = parsed.get("zip")
    if not city and parsed.get("city"):
        city = parsed.get("city")
    if not address1 and parsed.get("address1"):
        address1 = parsed.get("address1")
    if not address2 and parsed.get("address2"):
        candidate = parsed.get("address2") or ""
        if city and candidate.strip().lower() == city.strip().lower():
            candidate = ""
        if candidate:
            address2 = candidate
    if not address3 and parsed.get("address3"):
        address3 = parsed.get("address3")
    if not country and parsed.get("country"):
        country = _safe_country(parsed.get("country"))

    full_address = _full_address_from_components(
        {
            "address1": address1,
            "address2": address2,
            "address3": address3,
            "city": city,
            "state": state_province,
            "zip": zip_code,
        }
    )
    if full_address_raw and not full_address:
        full_address = full_address_raw

    return {
        "row_id": page.get("id") or "",
        "id": page.get("id") or "",
        "medical_facility_id": facility_id or "",
        "name": name or facility_id or "Unnamed Facility",
        "facility_type": facility_type,
        "address": full_address,
        "address1": address1,
        "address2": address2,
        "address3": address3,
        "city": city,
        "state": state_province or state_val,
        "zip": zip_code,
        "country": country,
        "county": county or parsed.get("county"),
        "borough": borough or parsed.get("borough"),
        "state_original": state_val,
        "phone": phone_val,
        "hours": _build_hours(props),
        "website": _url(props, "Website"),
        "google_maps_url": _url(props, "Google Maps URL"),
        "distance": distance_val,
        "place_types": [facility_type] if facility_type else [],
        "place_id": _rich_text(props, "Place_ID"),
        "notion_url": page.get("url") or "",
    }


def _clean_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _build_filter(filters: Dict[str, str]) -> Dict[str, Any] | None:
    clauses: List[Dict[str, Any]] = []

    name_contains = _clean_str(filters.get("name_contains"))
    if name_contains:
        clauses.append({"property": "Name", "rich_text": {"contains": name_contains}})

    address_contains = _clean_str(filters.get("address_contains"))
    if address_contains:
        clauses.append({"property": "Address", "rich_text": {"contains": address_contains}})

    state_value = _clean_str(filters.get("state"))
    if state_value:
        clauses.append({"property": "State / Province", "rich_text": {"equals": state_value}})

    facility_type = _clean_str(filters.get("facility_type"))
    if facility_type:
        clauses.append({"property": "Type", "select": {"equals": facility_type}})

    if not clauses:
        return None

    return {"and": clauses}


SORT_MAP: Dict[str, Dict[str, str]] = {
    "name_asc": {"property": "Name", "direction": "ascending"},
    "name_desc": {"property": "Name", "direction": "descending"},
    "type": {"property": "Type", "direction": "ascending"},
    "state": {"property": "State / Province", "direction": "ascending"},
}


def _build_sorts(sorts: List[str] | None) -> List[Dict[str, str]]:
    if not sorts:
        return []

    sort_blocks: List[Dict[str, str]] = []
    for value in sorts:
        if not value:
            continue
        block = SORT_MAP.get(value)
        if not block:
            raise ValueError(f"Unsupported sort value: {value}")
        sort_blocks.append(block)
    return sort_blocks


async def create_medical_facility_page(properties: Dict[str, Any]) -> Dict[str, Any]:
    db_id = Config.MEDICAL_FACILITIES_DB
    token = Config.NOTION_TOKEN
    if not token or not db_id:
        raise RuntimeError("Missing NOTION_TOKEN or MEDICAL_FACILITIES_DB")

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    url = "https://api.notion.com/v1/pages"
    payload = {"parent": {"database_id": db_id}, "properties": properties}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def _query_notion(filter_block: Dict[str, Any] | None, sorts: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    db_id = Config.MEDICAL_FACILITIES_DB
    token = Config.NOTION_TOKEN
    if not token or not db_id:
        raise RuntimeError("Missing NOTION_TOKEN or MEDICAL_FACILITIES_DB")

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    items: List[Dict[str, Any]] = []
    start_cursor: str | None = None

    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            payload: Dict[str, Any] = {"page_size": PAGE_SIZE}
            if filter_block:
                payload["filter"] = filter_block
            if sorts:
                payload["sorts"] = sorts
            if start_cursor:
                payload["start_cursor"] = start_cursor

            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            items.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            start_cursor = data.get("next_cursor")

    return items


async def update_medical_facility_page(page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    token = Config.NOTION_TOKEN
    if not token:
        raise RuntimeError("Missing NOTION_TOKEN")

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"properties": properties}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def find_medical_facility_by_place_id(place_id: str) -> Optional[Dict[str, Any]]:
    """Find a medical facility by its Google Place ID."""
    if not place_id:
        return None
    filter_block = {"property": "Place_ID", "rich_text": {"equals": place_id}}
    results = await _query_notion(filter_block=filter_block, sorts=[])
    if results:
        return results[0]
    return None


async def fetch_medical_facility_pages_raw() -> List[Dict[str, Any]]:
    """Return raw Medical Facilities pages for maintenance workflows."""
    return await _query_notion(filter_block=None, sorts=[])


async def search_medical_facilities(filters: Dict[str, str], sorts: List[str]) -> List[Dict[str, Any]]:
    filter_block = _build_filter(filters)
    sort_blocks = _build_sorts(sorts)
    pages = await _query_notion(filter_block=filter_block, sorts=sort_blocks)
    return [normalize_facility(p) for p in pages]


async def fetch_and_cache_medical_facilities() -> List[Dict[str, Any]]:
    log_job("facilities", "cache_refresh", "start", "operation=facilities_cache_refresh")
    pages = await _query_notion(filter_block=None, sorts=[])
    normalized = [normalize_facility(p) for p in pages]
    payload = {
        "timestamp": _utc_now(),
        "version": CACHE_SCHEMA_VERSION,
        "normalized": normalized,
        "raw": pages,
    }
    await save_facilities_cache(payload)
    log_job(
        "facilities",
        "cache_refresh",
        "success",
        f"operation=facilities_cache_refresh result_count={len(normalized)}",
    )
    return normalized


async def get_cached_medical_facilities(max_age_seconds: int = 3600) -> Dict[str, Any]:
    _ = max_age_seconds  # placeholder for future staleness-aware logic
    cache = await load_facilities_cache()
    if cache and cache.get("version") != CACHE_SCHEMA_VERSION:
        log_job(
            "facilities",
            "cache_version_mismatch",
            "error",
            f"operation=facilities_cache_load version={cache.get('version')} expected={CACHE_SCHEMA_VERSION}",
        )
        return {}
    if cache:
        log_job(
            "facilities",
            "cache_load",
            "success",
            f"operation=facilities_cache_load count={len(cache.get('normalized', []))}",
        )
    else:
        log_job("facilities", "cache_load", "error", "operation=facilities_cache_load missing")
    return cache


async def fetch_all_medical_facilities(limit: int, max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS) -> List[Dict[str, Any]]:
    if limit < 1:
        raise ValueError("Limit must be at least 1")

    cache = await load_facilities_cache()
    normalized = cache.get("normalized") if isinstance(cache, dict) else None
    if isinstance(normalized, list) and not is_cache_stale(cache, max_age_seconds=max_age_seconds):
        return normalized[:limit]

    log_job("facilities", "cache_refresh", "start", "operation=facilities_cache_refresh reason=stale_or_missing")
    refreshed = await fetch_and_cache_medical_facilities()
    return refreshed[:limit]
