from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.services.address_parser import parse_address
from app.services.cache_utils import DEFAULT_MAX_AGE_SECONDS, _utc_now, is_cache_stale, load_locations_cache, save_locations_cache
from app.services.logger import log_job
from app.services.location_status_utils import STATUS_MATCHED, STATUS_READY, STATUS_UNRESOLVED, log_status_applied
from config import Config

NOTION_VERSION = "2022-06-28"
PAGE_SIZE = 100
DEFAULT_COUNTRY = "US"
HEX_RE = re.compile(r"[0-9a-fA-F]{32}")
_cached_master_locations: Optional[Dict[str, Any]] = None
production_locations_cache: List[Dict[str, Any]] = []
production_locations_cache_ts: Optional[float] = None
PROD_CACHE_TTL = 60  # seconds


def _rich_text(props: Dict[str, Any], key: str) -> str:
    arr = props.get(key, {}).get("rich_text", [])
    return " ".join([a.get("plain_text", "") for a in arr if isinstance(a, dict)]) if arr else ""


def _title(props: Dict[str, Any], key: str) -> str:
    arr = props.get(key, {}).get("title", [])
    return " ".join([a.get("plain_text", "") for a in arr if isinstance(a, dict)]) if arr else ""


def _status(props: Dict[str, Any], key: str) -> str:
    status_obj = props.get(key, {}).get("status") or {}
    return status_obj.get("name") or ""


def _number(props: Dict[str, Any], key: str) -> Optional[float]:
    num = props.get(key, {}).get("number")
    return float(num) if num is not None else None


def _relation_ids(props: Dict[str, Any], key: str) -> List[str]:
    rels = props.get(key, {}).get("relation") or []
    return [rel.get("id") for rel in rels if rel.get("id")]


def _rt(value: str) -> Dict[str, Any]:
    return {"rich_text": [{"text": {"content": value}}]}


def _title_prop(value: str) -> Dict[str, Any]:
    return {"title": [{"text": {"content": value}}]}


def _status_prop(value: str) -> Dict[str, Any]:
    return {"status": {"name": value}}


def _safe_country(value: Optional[str]) -> str:
    return (value or DEFAULT_COUNTRY).upper()


def build_full_address(components: Dict[str, Optional[str]]) -> str:
    lines: List[str] = []
    for key in ("address1", "address2", "address3"):
        val = components.get(key)
        if val:
            lines.append(str(val).strip())

    city = (components.get("city") or "").strip()
    state = (components.get("state") or "").strip()
    postal = (components.get("zip") or "").strip()

    city_line_parts: List[str] = []
    if city:
        city_line_parts.append(city)
    if state:
        city_line_parts.append(state if not city else f"{state}")
    if postal:
        # ensure spacing between state and postal
        joined = " ".join([p for p in [state, postal] if p]).strip()
        if city and state:
            city_line_parts = [f"{city}, {joined}"]
        elif city and postal:
            city_line_parts = [f"{city} {postal}"]
        elif joined:
            city_line_parts = [joined]
    if not city_line_parts and city and state:
        city_line_parts.append(f"{city}, {state}")
    if city_line_parts and not lines and city_line_parts[0]:
        # no address lines but we have city/state/zip
        lines.append(city_line_parts[0])
    elif city_line_parts:
        lines.append(city_line_parts[0])

    return "\n".join([line for line in lines if line]).strip()


def resolve_status(place_id: Optional[str], matched: bool, explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    if matched:
        return STATUS_MATCHED
    if place_id:
        return STATUS_READY
    return STATUS_UNRESOLVED


def build_location_properties(
    components: Dict[str, Optional[str]],
    production_id: str,
    place_id: Optional[str] = None,
    place_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    status: Optional[str] = None,
    matched: bool = False,
    matched_master_id: Optional[str] = None,
) -> Dict[str, Any]:
    country = _safe_country(components.get("country"))
    payload = {
        "address1": components.get("address1"),
        "address2": components.get("address2"),
        "address3": components.get("address3"),
        "city": components.get("city"),
        "state": components.get("state"),
        "zip": components.get("zip"),
        "country": country,
        "county": components.get("county"),
        "borough": components.get("borough"),
    }
    full_address = build_full_address(payload)
    practical_name = place_name or components.get("address1") or ""
    resolved_status = resolve_status(place_id, matched, status)
    log_status_applied(status, resolved_status, place_id, matched, status)

    title_value = full_address or practical_name or f"Location for {production_id}"
    title_value = title_value[:200]
    props: Dict[str, Any] = {
        "ProdLocID": _title_prop(title_value),
        "Location Name": _rt(title_value),
        "Practical Name": _rt(practical_name[:200] if practical_name else ""),
        "Full Address": _rt(full_address),
        "Address 1": _rt(payload["address1"] or ""),
        "Address 2": _rt(payload["address2"] or ""),
        "Address 3": _rt(payload["address3"] or ""),
        "City": _rt(payload["city"] or ""),
        "State / Province": _rt(payload["state"] or ""),
        "ZIP / Postal Code": _rt(payload["zip"] or ""),
        "Country": _rt(country),
        "County": _rt(payload["county"] or ""),
        "Borough": _rt(payload["borough"] or ""),
        "ProductionID": _rt(production_id or ""),
        "Place_ID": _rt(place_id or ""),
        "Status": _status_prop(resolved_status),
        "Latitude": {"number": latitude},
        "Longitude": {"number": longitude},
    }
    if matched_master_id:
        props["LocationsMasterID"] = {"relation": [{"id": matched_master_id}]}
    return props


def normalize_location(page: Dict[str, Any]) -> Dict[str, Any]:
    props = page.get("properties") or {}
    prod_loc_id = ""
    prop_prod_loc = props.get("ProdLocID") or {}
    if prop_prod_loc.get("title"):
        prod_loc_id = "".join([t.get("plain_text", "") for t in prop_prod_loc.get("title", []) if isinstance(t, dict)])
    elif prop_prod_loc.get("rich_text"):
        prod_loc_id = "".join([t.get("plain_text", "") for t in prop_prod_loc.get("rich_text", []) if isinstance(t, dict)])

    practical_name = _rich_text(props, "Practical Name")
    name = practical_name or _rich_text(props, "Location Name") or prod_loc_id
    address1 = _rich_text(props, "Address 1")
    address2 = _rich_text(props, "Address 2")
    address3 = _rich_text(props, "Address 3")
    city = _rich_text(props, "City")
    state = _rich_text(props, "State / Province") or _rich_text(props, "State")
    zip_code = _rich_text(props, "ZIP / Postal Code") or _rich_text(props, "ZIP")
    country = _safe_country(_rich_text(props, "Country"))
    county = _rich_text(props, "County")
    borough = _rich_text(props, "Borough")
    existing_full_address = _rich_text(props, "Full Address")
    status = _status(props, "Status")
    parsed = parse_address(existing_full_address)
    if not state and parsed.get("state"):
        state = parsed.get("state")
    if not zip_code and parsed.get("zip"):
        zip_code = parsed.get("zip")
    if not city and parsed.get("city"):
        city = parsed.get("city")
    if not address1 and parsed.get("address1"):
        address1 = parsed.get("address1")
    if not address2 and parsed.get("address2"):
        address2 = parsed.get("address2")
    if not address3 and parsed.get("address3"):
        address3 = parsed.get("address3")
    if not country and parsed.get("country"):
        country = _safe_country(parsed.get("country"))

    full_address = build_full_address(
        {
            "address1": address1,
            "address2": address2,
            "address3": address3,
            "city": city,
            "state": state,
            "zip": zip_code,
        }
    )
    if existing_full_address and not full_address:
        full_address = existing_full_address
    production_id = ""
    prop_prod_rel = props.get("ProductionID") or {}
    rels = prop_prod_rel.get("relation") or []
    if isinstance(rels, list) and rels:
        production_id = rels[0].get("id") or ""

    return {
        "row_id": page.get("id") or "",
        "id": page.get("id") or "",
        "prod_loc_id": prod_loc_id,
        "name": name or prod_loc_id or "Unnamed Location",
        "address": full_address,
        "address1": address1,
        "address2": address2,
        "address3": address3,
        "city": city,
        "state": state,
        "zip": zip_code,
        "country": country,
        "county": county or parsed.get("county"),
        "borough": borough or parsed.get("borough"),
        "status": status,
        "production_id": production_id or "",
        "place_id": _rich_text(props, "Place_ID"),
        "latitude": _number(props, "Latitude"),
        "longitude": _number(props, "Longitude"),
        "locations_master_ids": _relation_ids(props, "LocationsMasterID"),
    }


def _extract_title_generic(props: Dict[str, Any]) -> str:
    for value in props.values():
        if isinstance(value, dict) and value.get("type") == "title":
            items = value.get("title") or []
            if items:
                return items[0].get("plain_text") or items[0].get("text", {}).get("content", "") or ""
    return ""


def get_locations_db_id_from_url(url: str) -> str:
    """
    Extract 32-character hex DB id from a Notion DB URL.
    Example: https://www.notion.so/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=yyyyyy
    """
    if not url:
        return ""
    match = HEX_RE.search(url)
    return match.group(0) if match else ""


async def _query_productions_master(db_id: str) -> List[Dict[str, Any]]:
    headers = _headers()
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    items: List[Dict[str, Any]] = []
    start_cursor: str | None = None
    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            payload: Dict[str, Any] = {"page_size": PAGE_SIZE}
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


async def load_all_production_locations(productions_master_db_id: str, refresh: bool = False) -> List[Dict[str, Any]]:
    """Aggregate all production-specific locations across all productions."""
    global production_locations_cache, production_locations_cache_ts

    if not productions_master_db_id:
        raise RuntimeError("Missing productions master DB id")

    cache_valid = (
        production_locations_cache
        and production_locations_cache_ts
        and (time.time() - production_locations_cache_ts) < PROD_CACHE_TTL
    )
    print(f"[production_cache] refresh={refresh} using_cache={cache_valid}")

    if (
        not refresh
        and production_locations_cache
        and production_locations_cache_ts
        and (time.time() - production_locations_cache_ts) < PROD_CACHE_TTL
    ):
        return production_locations_cache

    try:
        productions = await _query_productions_master(productions_master_db_id)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to load productions master: {exc}") from exc

    all_locations: List[Dict[str, Any]] = []
    for prod in productions:
        props = prod.get("properties") or {}
        locations_table_prop = props.get("Locations Table") or {}
        locations_url = locations_table_prop.get("url") or ""
        prod_title = _extract_title_generic(props)
        db_id = get_locations_db_id_from_url(locations_url)
        if not db_id:
            continue
        try:
            pages = await _query_notion(filter_block=None, sorts=[], db_id=db_id)
            normalized_rows = [normalize_location(p) for p in pages]
            for row in normalized_rows:
                if not row.get("production_id") and prod_title:
                    row["production_id"] = prod_title
            all_locations.extend(normalized_rows)
        except Exception as exc:  # noqa: BLE001
            log_job("locations", "load_production_locations", "error", f"db_id={db_id} error={exc}")
            continue

    production_locations_cache = all_locations
    production_locations_cache_ts = time.time()
    return all_locations


def clear_production_locations_cache() -> None:
    global production_locations_cache_ts
    production_locations_cache.clear()
    production_locations_cache_ts = None


async def load_locations_master() -> List[Dict[str, Any]]:
    """Load and normalize all rows from the Locations Master Notion DB."""
    db_id = Config.LOCATIONS_MASTER_DB
    if not db_id:
        raise RuntimeError("Missing LOCATIONS_MASTER_DB environment variable")
    pages = await _query_notion(filter_block=None, sorts=[], db_id=db_id)
    normalized = [normalize_location(p) for p in pages]
    return normalized


async def get_locations_master_cached(refresh: bool = False) -> List[Dict[str, Any]]:
    """Return cached Locations Master rows, refreshing when requested or missing."""
    global _cached_master_locations
    if refresh or not _cached_master_locations:
        master_rows = await load_locations_master()
        _cached_master_locations = {"normalized": master_rows, "ts": datetime.utcnow().isoformat()}
    return _cached_master_locations.get("normalized", [])


def _headers() -> Dict[str, str]:
    token = Config.NOTION_TOKEN
    if not token:
        raise RuntimeError("Missing NOTION_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


async def _query_notion(
    filter_block: Dict[str, Any] | None = None,
    sorts: List[Dict[str, str]] | None = None,
    db_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    database_id = db_id or Config.LOCATIONS_MASTER_DB
    if not Config.NOTION_TOKEN or not database_id:
        raise RuntimeError("Missing NOTION_TOKEN or LOCATIONS_MASTER_DB")

    headers = _headers()
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
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


async def fetch_location_pages_raw() -> List[Dict[str, Any]]:
    """Return raw Location pages from Notion without normalization (used by backfill jobs)."""
    return await _query_notion(filter_block=None, sorts=[])


async def create_location_page(properties: Dict[str, Any]) -> Dict[str, Any]:
    db_id = Config.LOCATIONS_MASTER_DB
    if not db_id:
        raise RuntimeError("Missing LOCATIONS_MASTER_DB")

    payload = {"parent": {"database_id": db_id}, "properties": properties}
    headers = _headers()
    url = "https://api.notion.com/v1/pages"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def update_location_page(page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    headers = _headers()
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"properties": properties}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def fetch_and_cache_locations() -> List[Dict[str, Any]]:
    log_job("locations", "cache_refresh", "start", "operation=locations_cache_refresh")
    pages = await _query_notion(filter_block=None, sorts=[])
    normalized = [normalize_location(p) for p in pages]
    payload = {
        "timestamp": _utc_now(),
        "normalized": normalized,
        "raw": pages,
    }
    await save_locations_cache(payload)
    log_job(
        "locations",
        "cache_refresh",
        "success",
        f"operation=locations_cache_refresh result_count={len(normalized)}",
    )
    return normalized


async def get_cached_locations(max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS) -> Dict[str, Any]:
    _ = max_age_seconds  # placeholder for future staleness-aware logic
    cache = await load_locations_cache()
    if cache:
        log_job(
            "locations",
            "cache_load",
            "success",
            f"operation=locations_cache_load count={len(cache.get('normalized', []))}",
        )
    else:
        log_job("locations", "cache_load", "error", "operation=locations_cache_load missing")
    return cache


async def fetch_all_locations(limit: int, max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS) -> List[Dict[str, Any]]:
    if limit < 1:
        raise ValueError("Limit must be at least 1")

    cache = await load_locations_cache()
    normalized = cache.get("normalized") if isinstance(cache, dict) else None
    if isinstance(normalized, list) and not is_cache_stale(cache, max_age_seconds=max_age_seconds):
        return normalized[:limit]

    log_job("locations", "cache_refresh", "start", "operation=locations_cache_refresh reason=stale_or_missing")
    refreshed = await fetch_and_cache_locations()
    return refreshed[:limit]


def _clean_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _build_filter(filters: Dict[str, str]) -> Dict[str, Any] | None:
    clauses: List[Dict[str, Any]] = []

    name_contains = _clean_str(filters.get("name_contains"))
    if name_contains:
        clauses.append({"property": "Location Name", "rich_text": {"contains": name_contains}})

    address_contains = _clean_str(filters.get("address_contains"))
    if address_contains:
        clauses.append({"property": "Full Address", "rich_text": {"contains": address_contains}})

    city = _clean_str(filters.get("city"))
    if city:
        clauses.append({"property": "City", "rich_text": {"equals": city}})

    state = _clean_str(filters.get("state"))
    if state:
        clauses.append({"property": "State / Province", "rich_text": {"equals": state}})

    production_id = _clean_str(filters.get("production_id"))
    if production_id:
        clauses.append({"property": "ProductionID", "rich_text": {"equals": production_id}})

    if not clauses:
        return None

    return {"and": clauses}


SORT_MAP: Dict[str, Dict[str, str]] = {
    "name_asc": {"property": "Location Name", "direction": "ascending"},
    "name_desc": {"property": "Location Name", "direction": "descending"},
    "city": {"property": "City", "direction": "ascending"},
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


async def search_locations(filters: Dict[str, str], sorts: List[str]) -> List[Dict[str, Any]]:
    filter_block = _build_filter(filters)
    sort_blocks = _build_sorts(sorts)
    pages = await _query_notion(filter_block=filter_block, sorts=sort_blocks)
    return [normalize_location(p) for p in pages]
