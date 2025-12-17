from __future__ import annotations
import json
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import httpx
import re

from app.services.debug_logger import debug_log, debug_enabled
from app.services.ingestion_normalizer import _components_from_google, _google_geometry, normalize_components
from app.services.notion_schema_utils import fetch_database
from app.services.logger import log_job
from app.services.master_cache import load_master_cache
from app.services.notion_locations import (
    _headers,
    build_full_address,
    create_location_page,
    fetch_production_locations,
    resolve_status,
    update_location_page,
    resolve_production_for_locations_db,
)
from config import Config

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PLACE_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

MASTER_SCHEMA_CACHE: Dict[str, Any] | None = None
MASTER_TITLE_PROP: Optional[str] = None
PSL_SCHEMA_FIELDS: Dict[str, Dict[str, str]] = {}

PRODLOC_RE = re.compile(r"^([A-Za-z0-9]+?)(\d+)$")


def _rt(value: str) -> Dict[str, Any]:
    return {"rich_text": [{"text": {"content": value}}]}


def _url(value: str) -> Dict[str, Any]:
    return {"url": value}


def _multi(values: List[str]) -> Dict[str, Any]:
    return {"multi_select": [{"name": v} for v in values]}


def _strip_psl_phone(props: Dict[str, Any]) -> Dict[str, Any]:
    """Remove International Phone from PSL-bound payloads (LM-only field)."""
    props.pop("International Phone", None)
    props.pop("international_phone", None)
    return props


def _address_key(fields: Dict[str, Any]) -> Tuple[str, ...]:
    return tuple((fields.get(k) or "").strip().lower() for k in ("address1", "city", "state", "zip", "country"))


LOC_RE = re.compile(r"^LOC(\d+)$")


def _loc_title_from_row(row: Dict[str, Any]) -> str:
    return (row.get("prod_loc_id") or row.get("name") or "").strip()


def _build_prodloc_counters(rows: List[Dict[str, Any]], prefix: str | None) -> Dict[str, int]:
    """Return prefix -> highest numeric suffix seen for ProdLocID values."""
    counters: Dict[str, int] = {}
    if not prefix:
        return counters
    prefix_upper = prefix.upper()
    for row in rows:
        value = (row.get("prod_loc_id") or "").strip()
        match = PRODLOC_RE.match(value)
        if not match:
            continue
        if match.group(1).upper() != prefix_upper:
            continue
        try:
            counters[prefix_upper] = max(counters.get(prefix_upper, 0), int(match.group(2)))
        except ValueError:
            continue
    return counters


def _next_loc_title(master_cache: Dict[str, Any]) -> str:
    """Generate next LOC### title based on existing LM rows."""
    max_num = 0
    for row in master_cache.get("rows", []):
        title = _loc_title_from_row(row)
        m = LOC_RE.match(title)
        if m:
            try:
                max_num = max(max_num, int(m.group(1)))
            except ValueError:
                continue
    next_num = max_num + 1
    width = 3 if next_num < 1000 else 4
    return f"LOC{next_num:0{width}d}"


async def _load_master_schema() -> Dict[str, Any]:
    """Fetch and cache Locations Master schema for safe writes."""
    global MASTER_SCHEMA_CACHE, MASTER_TITLE_PROP
    if MASTER_SCHEMA_CACHE and MASTER_TITLE_PROP:
        return MASTER_SCHEMA_CACHE

    db_id = Config.LOCATIONS_MASTER_DB
    if not db_id:
        raise RuntimeError("Missing LOCATIONS_MASTER_DB")
    headers = _headers()
    url = f"https://api.notion.com/v1/databases/{db_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    props = data.get("properties") or {}
    MASTER_SCHEMA_CACHE = props
    for name, definition in props.items():
        if isinstance(definition, dict) and definition.get("type") == "title":
            MASTER_TITLE_PROP = name
            break
    if not MASTER_TITLE_PROP:
        raise RuntimeError("Locations Master title property not found.")
    return props


async def _google_request(url: str, params: Dict[str, Any], *, allow_zero: bool = False) -> Dict[str, Any]:
    api_key = Config.GOOGLE_MAPS_API_KEY
    if not api_key:
        raise RuntimeError("Missing GOOGLE_MAPS_API_KEY")
    payload = dict(params)
    payload["key"] = api_key
    async with httpx.AsyncClient(timeout=12.0) as client:
        resp = await client.get(url, params=payload)
    resp.raise_for_status()
    data = resp.json()
    status = data.get("status")
    if status == "ZERO_RESULTS" and allow_zero:
        return data
    if status != "OK":
        raise ValueError(f"Google API error: {status or 'unknown'}")
    return data


async def _geocode(address: str) -> Dict[str, Any] | None:
    data = await _google_request(GEOCODE_URL, {"address": address}, allow_zero=True)
    results = data.get("results") or []
    if not results:
        return None
    if len(results) != 1:
        raise ValueError("Ambiguous geocode result")
    return results[0]


async def _place_details(place_id: str) -> Dict[str, Any]:
    data = await _google_request(
        PLACE_DETAILS_URL,
        {"place_id": place_id, "fields": "place_id,name,formatted_address,address_component,geometry,url,vicinity,international_phone_number,website,types"},
    )
    result = data.get("result") or {}
    if not result:
        raise ValueError("Place details missing result")
    return result


async def _place_search(query: str) -> Dict[str, Any] | None:
    data = await _google_request(PLACE_SEARCH_URL, {"query": query}, allow_zero=True)
    results = data.get("results") or []
    if not results:
        return None
    if len(results) != 1:
        raise ValueError("Ambiguous place search result")
    return results[0]


def _matches_anchor(components: Dict[str, Any], anchors: Dict[str, str]) -> bool:
    for key in ("city", "state", "zip", "country"):
        anchor_val = (anchors.get(key) or "").strip().lower()
        comp_val = (components.get(key) or "").strip().lower()
        if anchor_val and comp_val and anchor_val != comp_val:
            return False
    return True


def _extract_google_fields(result: Dict[str, Any], anchors: Dict[str, str]) -> Dict[str, Any]:
    components_raw = _components_from_google(result)
    components = normalize_components(components_raw)
    formatted_address_google = result.get("formatted_address")
    full_address = build_full_address(components)
    latitude, longitude = _google_geometry(result)
    types_raw = result.get("types") or []
    filtered_types = [t for t in types_raw if t not in {"establishment", "point_of_interest"}]
    return {
        "place_id": result.get("place_id"),
        "practical_name": result.get("name") or "",
        "formatted_address_google": formatted_address_google,
        "full_address": formatted_address_google or full_address,
        "address1": components.get("address1"),
        "address2": components.get("address2"),
        "address3": components.get("address3"),
        "city": components.get("city"),
        "state": components.get("state"),
        "zip": components.get("zip"),
        "country": components.get("country"),
        "county": components.get("county"),
        "borough": components.get("borough"),
        "latitude": latitude,
        "longitude": longitude,
        "google_maps_url": result.get("url"),
        "vicinity": result.get("vicinity"),
        "international_phone": result.get("international_phone_number"),
        "website": result.get("website"),
        "types": filtered_types,
        "anchors_match": _matches_anchor(components, anchors),
    }


def _build_master_properties(google_fields: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    props: Dict[str, Any] = {}

    def add(prop: str, payload: Dict[str, Any]) -> None:
        if prop in schema:
            props[prop] = payload

    if google_fields.get("full_address"):
        add("Full Address", _rt(str(google_fields["full_address"])))
    if google_fields.get("formatted_address_google"):
        add("formatted_address_google", _rt(str(google_fields["formatted_address_google"])))
    if google_fields.get("place_id"):
        add("Place_ID", _rt(str(google_fields["place_id"])))
    if google_fields.get("practical_name"):
        add("Practical Name", _rt(str(google_fields["practical_name"])))
    if google_fields.get("address1"):
        add("address1", _rt(str(google_fields["address1"])))
    if google_fields.get("address2"):
        add("address2", _rt(str(google_fields["address2"])))
    if google_fields.get("address3"):
        add("address3", _rt(str(google_fields["address3"])))
    if google_fields.get("city"):
        add("city", _rt(str(google_fields["city"])))
    if google_fields.get("state"):
        add("state", _rt(str(google_fields["state"])))
    if google_fields.get("zip"):
        add("zip", _rt(str(google_fields["zip"])))
    if google_fields.get("country"):
        add("country", _rt(str(google_fields["country"])))
    if google_fields.get("county"):
        add("county", _rt(str(google_fields["county"])))
    if google_fields.get("borough"):
        add("borough", _rt(str(google_fields["borough"])))
    if google_fields.get("vicinity"):
        add("Vicinity", _rt(str(google_fields["vicinity"])))
    if google_fields.get("google_maps_url"):
        add("Google Maps URL", _url(str(google_fields["google_maps_url"])))
    if google_fields.get("website"):
        add("Website", _url(str(google_fields["website"])))
    if google_fields.get("international_phone"):
        # Locations Master expects phone_number type
        if "International Phone" in schema:
            props["International Phone"] = {"phone_number": str(google_fields["international_phone"])}
    if google_fields.get("types"):
        add("Types", _multi(list(google_fields["types"])))
    if google_fields.get("latitude") is not None:
        add("Latitude", {"number": float(google_fields["latitude"])})
    if google_fields.get("longitude") is not None:
        add("Longitude", {"number": float(google_fields["longitude"])})
    return props


def _build_psl_update_properties(
    google_fields: Dict[str, Any],
    matched_master_id: str | None,
    production_page_id: str | None = None,
    prodloc_id: str | None = None,
) -> Dict[str, Any]:
    """Build PSL payload; actual write filters by schema/types later."""
    if "international_phone" in google_fields or "International Phone" in google_fields:
        google_fields = {k: v for k, v in google_fields.items() if k not in {"international_phone", "International Phone"}}
    props: Dict[str, Any] = {}
    if google_fields.get("place_id"):
        props["Place_ID"] = _rt(str(google_fields["place_id"]))
    if matched_master_id:
        props["LocationsMasterID"] = {"relation": [{"id": matched_master_id}]}
    if production_page_id:
        props["ProductionID"] = {"relation": [{"id": production_page_id}]}
    if prodloc_id:
        props["ProdLocID"] = {"title": [{"text": {"content": prodloc_id}}]}
    if google_fields.get("practical_name"):
        props["Practical Name"] = _rt(str(google_fields["practical_name"]))
    if google_fields.get("full_address"):
        props["Full Address"] = _rt(str(google_fields["full_address"]))
    if google_fields.get("formatted_address_google"):
        props["formatted_address_google"] = _rt(str(google_fields["formatted_address_google"]))
    if google_fields.get("address1"):
        props["address1"] = _rt(str(google_fields["address1"]))
    if google_fields.get("address2"):
        props["address2"] = _rt(str(google_fields["address2"]))
    if google_fields.get("address3"):
        props["address3"] = _rt(str(google_fields["address3"]))
    if google_fields.get("city"):
        props["city"] = _rt(str(google_fields["city"]))
    if google_fields.get("state"):
        props["state"] = _rt(str(google_fields["state"]))
    if google_fields.get("zip"):
        props["zip"] = _rt(str(google_fields["zip"]))
    if google_fields.get("country"):
        props["country"] = _rt(str(google_fields["country"]))
    if google_fields.get("county"):
        props["county"] = _rt(str(google_fields["county"]))
    if google_fields.get("borough"):
        props["borough"] = _rt(str(google_fields["borough"]))
    if google_fields.get("vicinity"):
        props["Vicinity"] = _rt(str(google_fields["vicinity"]))
    if google_fields.get("google_maps_url"):
        props["Google Maps URL"] = _url(str(google_fields["google_maps_url"]))
    if google_fields.get("website"):
        props["Website"] = _url(str(google_fields["website"]))
    if google_fields.get("types"):
        props["Types"] = _multi(list(google_fields["types"]))
    if google_fields.get("latitude") is not None:
        props["Latitude"] = {"number": float(google_fields["latitude"])}
    if google_fields.get("longitude") is not None:
        props["Longitude"] = {"number": float(google_fields["longitude"])}
    return _strip_psl_phone(props)


def _update_cache_entry(master_cache: Dict[str, Any], google_fields: Dict[str, Any], master_id: str, loc_title: str | None = None) -> None:
    row = master_cache.get("place_id_index", {}).get(google_fields.get("place_id") or "")
    if not row:
        row = {"id": master_id}
        master_cache.setdefault("rows", []).append(row)
    row.update(
        {
            "id": master_id,
            "place_id": google_fields.get("place_id"),
            "address1": google_fields.get("address1"),
            "city": google_fields.get("city"),
            "state": google_fields.get("state"),
            "zip": google_fields.get("zip"),
            "country": google_fields.get("country"),
        }
    )
    if loc_title:
        row["prod_loc_id"] = loc_title
        row["name"] = loc_title
    pid = (google_fields.get("place_id") or "").strip()
    if pid:
        master_cache.setdefault("place_id_index", {})[pid] = row
    hash_key = _address_key(row)
    if any(hash_key):
        master_cache.setdefault("canonical_hash_index", {}).setdefault(hash_key, []).append(row)


async def _upsert_master_row(
    google_fields: Dict[str, Any],
    master_cache: Dict[str, Any],
    master_schema: Dict[str, Any],
) -> str:
    pid = google_fields.get("place_id") or ""
    if not pid:
        raise ValueError("Missing place_id for master upsert")

    master_row = master_cache.get("place_id_index", {}).get(pid)
    title_prop = MASTER_TITLE_PROP or "Name"
    props = _build_master_properties(google_fields, master_schema)

    if master_row:
        current_title = _loc_title_from_row(master_row)
        loc_title = current_title if LOC_RE.match(current_title) else _next_loc_title(master_cache)
        if loc_title:
            props[title_prop] = {"title": [{"text": {"content": loc_title}}]}
        await update_location_page(master_row.get("id") or "", props)
        _update_cache_entry(master_cache, google_fields, master_row.get("id") or "", loc_title=loc_title)
        return master_row.get("id") or ""

    await _load_master_schema()
    loc_title = _next_loc_title(master_cache)
    props[title_prop] = {"title": [{"text": {"content": str(loc_title)[:200]}}]}
    page = await create_location_page(props)
    master_id = page.get("id") or ""
    _update_cache_entry(master_cache, google_fields, master_id, loc_title=loc_title)
    return master_id


def _eligible(row: Dict[str, Any]) -> bool:
    if row.get("place_id"):
        return True
    has_address = bool(row.get("address")) or (row.get("address1") and row.get("city") and row.get("state"))
    anchors_present = any([(row.get("city") or "").strip(), (row.get("state") or "").strip(), (row.get("zip") or "").strip(), (row.get("address1") or "").strip()])
    has_practical_name = bool((row.get("practical_name") or "").strip() or (row.get("name") or "").strip())
    if has_address:
        return True
    return bool(has_practical_name and anchors_present)


def _anchors_from_row(row: Dict[str, Any]) -> Dict[str, str]:
    return {
        "city": (row.get("city") or row.get("city_raw") or "").strip(),
        "state": (row.get("state") or row.get("state_raw") or "").strip(),
        "zip": (row.get("zip") or row.get("zip_raw") or "").strip(),
        "country": (row.get("country") or row.get("country_raw") or "").strip(),
    }


def _filter_psl_payload(payload: Dict[str, Any], schema_props: Dict[str, str]) -> Tuple[Dict[str, Any], List[str]]:
    """Keep only fields present in schema with matching types; collect skipped reasons."""
    _strip_psl_phone(payload)
    filtered: Dict[str, Any] = {}
    skipped: List[str] = []
    expected_types: Dict[str, set[str]] = {
        "Place_ID": {"rich_text", "title"},
        "LocationsMasterID": {"relation"},
        "ProductionID": {"relation"},
        "ProdLocID": {"title"},
        "Practical Name": {"rich_text", "title"},
        "Full Address": {"rich_text"},
        "formatted_address_google": {"rich_text"},
        "address1": {"rich_text"},
        "address2": {"rich_text"},
        "address3": {"rich_text"},
        "city": {"rich_text"},
        "state": {"rich_text"},
        "zip": {"rich_text"},
        "country": {"rich_text"},
        "county": {"rich_text"},
        "borough": {"rich_text"},
        "Vicinity": {"rich_text"},
        "Google Maps URL": {"url"},
        "Website": {"url"},
        "Latitude": {"number"},
        "Longitude": {"number"},
        "Types": {"multi_select"},
    }
    for key, value in payload.items():
        expected_type = schema_props.get(key)
        if not expected_type:
            skipped.append(f"{key} (missing in schema)")
            continue
        allowed_types = expected_types.get(key)
        if allowed_types and expected_type not in allowed_types:
            skipped.append(f"{key} (type mismatch: schema={expected_type})")
            continue
        if not allowed_types:
            skipped.append(f"{key} (not allowed for PSL write)")
            continue
        filtered[key] = value
    return filtered, skipped


def _extract_http_error_body(exc: httpx.HTTPStatusError) -> str:
    """Return raw response body (if available) from an HTTPStatusError."""
    if exc.response is not None:
        try:
            return exc.response.text
        except Exception:  # noqa: BLE001
            return ""
    for arg in exc.args:
        if isinstance(arg, str) and arg.startswith("response_body="):
            return arg.partition("response_body=")[2]
    return ""


async def _enrich_row(
    row: Dict[str, Any],
    master_cache: Dict[str, Any],
    master_schema: Dict[str, Any],
    psl_schema_props: Dict[str, str],
    production_name: str,
    db_id: str,
    production_page_id: str | None,
    prodloc_prefix: str | None,
    prodloc_counters: Dict[str, int],
) -> Tuple[str, str]:
    anchors = _anchors_from_row(row)
    page_id = row.get("id") or ""
    label = row.get("prod_loc_id") or row.get("name") or ""
    prodloc_id_to_apply: str | None = None
    if prodloc_prefix:
        current = (row.get("prod_loc_id") or "").strip()
        match = PRODLOC_RE.match(current)
        if not match or match.group(1).upper() != prodloc_prefix.upper():
            next_num = prodloc_counters.get(prodloc_prefix.upper(), 0) + 1
            prodloc_counters[prodloc_prefix.upper()] = next_num
            prodloc_id_to_apply = f"{prodloc_prefix}{next_num:03d}"
    
    def log_request(props: Dict[str, Any]):
        if not debug_enabled():
            return
        log_payload = {
            "production_name": production_name,
            "psl_db_id": db_id,
            "psl_page_id": page_id,
            "psl_label": label,
            "payload": props,
        }
        debug_log("PSL_ENRICHMENT", f"PATCH /v1/pages/{page_id} PAYLOAD: {json.dumps(log_payload, indent=2)}")

    def log_success():
        if not debug_enabled():
            return
        debug_log("PSL_ENRICHMENT", f"PATCH /v1/pages/{page_id} SUCCESS")
        
    def log_failure(exc: httpx.HTTPStatusError):
        body = _extract_http_error_body(exc)
        if not debug_enabled():
            return body
        debug_log("PSL_ENRICHMENT", f"PATCH /v1/pages/{page_id} FAILED: {body}")
        return body

    try:
        if row.get("place_id"):
            details = await _place_details(str(row.get("place_id")))
            google_fields = _extract_google_fields(details, anchors)
            if not google_fields.get("anchors_match"):
                return "ambiguous", "place_id locality mismatch"
            master_id = await _upsert_master_row(google_fields, master_cache, master_schema)
            psl_props, skipped_fields = _filter_psl_payload(
                _build_psl_update_properties(
                    google_fields,
                    master_id,
                    production_page_id=production_page_id,
                    prodloc_id=prodloc_id_to_apply,
                ),
                psl_schema_props,
            )
            if not psl_props:
                reason = "no writable fields in PSL schema"
                if skipped_fields:
                    reason += f" (skipped: {', '.join(skipped_fields)})"
                return "ambiguous", reason
            try:
                final_props = _strip_psl_phone(psl_props)
                log_request(final_props)
                await update_location_page(page_id, final_props)
                log_success()
                reason = "refresh"
                if skipped_fields:
                    reason += f" (skipped: {', '.join(skipped_fields)})"
                return "enriched", reason
            except httpx.HTTPStatusError as exc:
                body = log_failure(exc)
                status_code = exc.response.status_code if exc.response else "unknown"
                return "error", f"psl_update_failed status={status_code} body={body} payload_keys={list(psl_props.keys())}"

        address_signal = row.get("address") or ""
        if not address_signal and row.get("address1") and row.get("city") and row.get("state"):
            address_signal = build_full_address(
                {
                    "address1": row.get("address1"),
                    "address2": row.get("address2"),
                    "address3": row.get("address3"),
                    "city": row.get("city"),
                    "state": row.get("state"),
                    "zip": row.get("zip"),
                    "country": row.get("country"),
                }
            )

        if address_signal:
            geo = await _geocode(address_signal)
            if not geo:
                return "ambiguous", "geocode yielded no results"
            google_fields = _extract_google_fields(geo, anchors)
            if not google_fields.get("anchors_match"):
                return "ambiguous", "geocode locality mismatch"
            if google_fields.get("place_id"):
                details = await _place_details(str(google_fields["place_id"]))
                google_fields = _extract_google_fields(details, anchors)
            master_id = await _upsert_master_row(google_fields, master_cache, master_schema)
            psl_props, skipped_fields = _filter_psl_payload(
                _build_psl_update_properties(
                    google_fields,
                    master_id,
                    production_page_id=production_page_id,
                    prodloc_id=prodloc_id_to_apply,
                ),
                psl_schema_props,
            )
            if not psl_props:
                reason = "no writable fields in PSL schema"
                if skipped_fields:
                    reason += f" (skipped: {', '.join(skipped_fields)})"
                return "ambiguous", reason
            try:
                final_props = _strip_psl_phone(psl_props)
                log_request(final_props)
                await update_location_page(page_id, final_props)
                log_success()
                reason = "address"
                if skipped_fields:
                    reason += f" (skipped: {', '.join(skipped_fields)})"
                return "enriched", reason
            except httpx.HTTPStatusError as exc:
                body = log_failure(exc)
                status_code = exc.response.status_code if exc.response else "unknown"
                return "error", f"psl_update_failed status={status_code} body={body} payload_keys={list(psl_props.keys())}"

        practical_name = (row.get("practical_name") or row.get("name") or "").strip()
        if practical_name:
            query_parts = [practical_name]
            if anchors.get("city"):
                query_parts.append(anchors["city"])
            if anchors.get("state"):
                query_parts.append(anchors["state"])
            if anchors.get("zip"):
                query_parts.append(anchors["zip"])
            query = ", ".join([p for p in query_parts if p])
            search_result = await _place_search(query)
            if not search_result:
                return "ambiguous", "no search results"
            google_fields = _extract_google_fields(search_result, anchors)
            if not google_fields.get("anchors_match"):
                return "ambiguous", "search locality mismatch"
            if google_fields.get("place_id"):
                details = await _place_details(str(google_fields["place_id"]))
                google_fields = _extract_google_fields(details, anchors)
            master_id = await _upsert_master_row(google_fields, master_cache, master_schema)
            psl_props, skipped_fields = _filter_psl_payload(
                _build_psl_update_properties(
                    google_fields,
                    master_id,
                    production_page_id=production_page_id,
                    prodloc_id=prodloc_id_to_apply,
                ),
                psl_schema_props,
            )
            if not psl_props:
                reason = "no writable fields in PSL schema"
                if skipped_fields:
                    reason += f" (skipped: {', '.join(skipped_fields)})"
                return "ambiguous", reason
            try:
                final_props = _strip_psl_phone(psl_props)
                log_request(final_props)
                await update_location_page(page_id, final_props)
                log_success()
                reason = "name"
                if skipped_fields:
                    reason += f" (skipped: {', '.join(skipped_fields)})"
                return "enriched", reason
            except httpx.HTTPStatusError as exc:
                body = log_failure(exc)
                status_code = exc.response.status_code if exc.response else "unknown"
                return "error", f"psl_update_failed status={status_code} body={body} payload_keys={list(psl_props.keys())}"

    except ValueError as exc:
        return "ambiguous", str(exc)
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, httpx.HTTPStatusError):
            body = _extract_http_error_body(exc)
            status_code = exc.response.status_code if getattr(exc, "response", None) is not None else "unknown"
            return "error", f"psl_update_failed status={status_code} body={body}"
        return "error", str(exc)

    return "not_ready", "insufficient signals"


async def stream_enrich_psl(db_id: str, production_label: str | None = None) -> AsyncGenerator[str, None]:
    """Stream enrichment progress for a single PSL (production locations) database."""
    if not db_id:
        yield "error: missing db_id"
        return

    try:
        master_schema = await _load_master_schema()
    except Exception as exc:  # noqa: BLE001
        yield f"error: failed to load master schema: {exc}"
        return

    if db_id in PSL_SCHEMA_FIELDS:
        psl_schema_props = PSL_SCHEMA_FIELDS[db_id]
    else:
        try:
            db_obj = await fetch_database(db_id)
            props = db_obj.get("properties") or {}
            psl_schema_props = {name: (definition.get("type") or "") for name, definition in props.items() if isinstance(definition, dict)}
            PSL_SCHEMA_FIELDS[db_id] = psl_schema_props
        except Exception as exc:  # noqa: BLE001
            yield f"error: failed to load PSL schema: {exc}"
            return

    try:
        rows = await fetch_production_locations(db_id, production_id=production_label)
    except Exception as exc:  # noqa: BLE001
        yield f"error: failed to load PSL rows: {exc}"
        return

    production_page_id: str | None = None
    prodloc_prefix: str | None = None
    try:
        production_page_id, prodloc_prefix = await resolve_production_for_locations_db(db_id)
    except Exception:
        production_page_id, prodloc_prefix = None, None
    if not prodloc_prefix:
        prodloc_prefix = (production_label or "").strip()
    if prodloc_prefix:
        prodloc_prefix = re.sub(r"\s+", "", prodloc_prefix).upper()
    prodloc_counters = _build_prodloc_counters(rows, prodloc_prefix)

    master_cache = await load_master_cache(refresh=True)
    total = len(rows)
    enriched = skipped_not_ready = ambiguous = errors = 0
    label = production_label or db_id
    yield f"Scanning {label} ({total} rows)..."

    for idx, row in enumerate(rows, start=1):
        yield f"Row {idx}/{total} - "
        if not _eligible(row):
            skipped_not_ready += 1
            yield "skipped (not ready)"
            continue
        status, reason = await _enrich_row(
            row,
            master_cache,
            master_schema,
            psl_schema_props,
            label,
            db_id,
            production_page_id,
            prodloc_prefix,
            prodloc_counters,
        )
        if status == "enriched":
            enriched += 1
            yield f"enriched via {reason}"
        elif status == "ambiguous":
            ambiguous += 1
            yield f"skipped (ambiguous: {reason})"
        elif status == "error":
            errors += 1
            pid = row.get("row_id") or row.get("id") or ""
            label = row.get("prod_loc_id") or row.get("name") or ""
            yield f"error on row {idx}/{total} page_id={pid} label={label}: {reason}"
        elif status == "not_ready":
            skipped_not_ready += 1
            yield "skipped (not ready)"
        else:
            errors += 1
            yield f"error: {reason}"

    yield f"Done. enriched={enriched} skipped_not_ready={skipped_not_ready} ambiguous={ambiguous} errors={errors}"
    log_job(
        "psl_enrichment",
        "run",
        "success",
        f"db_id={db_id} label={label} rows={total} enriched={enriched} not_ready={skipped_not_ready} ambiguous={ambiguous} errors={errors}",
    )
