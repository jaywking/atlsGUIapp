from __future__ import annotations

from typing import Any, AsyncGenerator, Dict

from app.services.debug_logger import debug_enabled, debug_log
from app.services.medical_facilities import (
    _build_mf_properties_from_google_place,
    _get_place_details,
    _get_next_mf_id,
    _is_er,
    _is_urgent_care,
    generate_nearby_medical_facilities,
)
from app.services.notion_locations import fetch_location_pages_raw, normalize_location
from app.services.notion_medical_facilities import fetch_medical_facility_pages_raw, update_medical_facility_page


async def stream_generate_medical_facilities_all() -> AsyncGenerator[str, None]:
    """Stream summary-only generation of medical facilities for eligible LM rows."""
    try:
        pages = await fetch_location_pages_raw()
    except Exception as exc:  # noqa: BLE001
        yield f"error: failed to load Locations Master: {exc}\n"
        return

    total = len(pages)
    yield f"Scanning Locations Master ({total} rows)...\n"

    counts: Dict[str, int] = {
        "eligible": 0,
        "processed": 0,
        "skipped_er": 0,
        "skipped_missing": 0,
        "errors": 0,
    }

    for page in pages:
        page_id = page.get("id") or ""
        props = page.get("properties") or {}
        er_rel = props.get("ER", {}).get("relation") or []
        if er_rel:
            counts["skipped_er"] += 1
            if debug_enabled():
                debug_log("MEDICAL_FACILITIES_RUN", f"skip (ER populated) lm={page_id} er_count={len(er_rel)}")
            continue

        normalized = normalize_location(page)
        lat = normalized.get("latitude")
        lon = normalized.get("longitude")
        place_id = normalized.get("place_id")

        has_coords = lat is not None and lon is not None
        has_place = bool(place_id)
        if not (has_coords or has_place):
            counts["skipped_missing"] += 1
            if debug_enabled():
                debug_log("MEDICAL_FACILITIES_RUN", f"skip (missing geo/place_id) lm={page_id}")
            continue

        counts["eligible"] += 1

        try:
            result = await generate_nearby_medical_facilities(page_id)
            if isinstance(result, dict) and result.get("status") == "error":
                counts["errors"] += 1
                if debug_enabled():
                    debug_log("MEDICAL_FACILITIES_RUN", f"error lm={page_id} message={result.get('message')}")
                continue
            counts["processed"] += 1
            if debug_enabled():
                debug_log("MEDICAL_FACILITIES_RUN", f"processed lm={page_id}")
        except Exception as exc:  # noqa: BLE001
            counts["errors"] += 1
            if debug_enabled():
                debug_log("MEDICAL_FACILITIES_RUN", f"error lm={page_id} exception={exc}")
            continue

    summary = (
        "Medical Facilities generation complete.\n"
        f"- Locations Master scanned: {total}\n"
        f"- Eligible for generation: {counts['eligible']}\n"
        f"- Generated/linked successfully: {counts['processed']}\n"
        f"- Skipped (already had ER): {counts['skipped_er']}\n"
        f"- Skipped (missing geo/place_id): {counts['skipped_missing']}\n"
        f"- Errors: {counts['errors']}\n"
    )
    yield summary


def _missing_field(props: Dict[str, Any], prop_name: str, prop_type: str) -> bool:
    prop = props.get(prop_name) or {}
    if prop_type == "rich_text":
        return not prop.get("rich_text")
    if prop_type == "url":
        return not prop.get("url")
    if prop_type == "phone_number":
        return not prop.get("phone_number")
    if prop_type == "number":
        return prop.get("number") is None
    if prop_type == "title":
        return not prop.get("title")
    if prop_type == "select":
        return not (prop.get("select") or {}).get("name")
    return True


def _extract_place_id(props: Dict[str, Any]) -> str:
    texts = props.get("Place_ID", {}).get("rich_text", []) or []
    return "".join([t.get("plain_text", "") for t in texts if isinstance(t, dict)]).strip()


def _extract_type(props: Dict[str, Any]) -> str:
    sel = props.get("Type", {}).get("select") or {}
    return (sel.get("name") or "").strip()


async def stream_backfill_medical_facilities_missing() -> AsyncGenerator[str, None]:
    """Backfill missing MF fields from Google Place Details (no overwrites)."""
    try:
        pages = await fetch_medical_facility_pages_raw()
    except Exception as exc:  # noqa: BLE001
        yield f"error: failed to load Medical Facilities: {exc}\n"
        return

    fields: Dict[str, str] = {
        "Friday Hours": "rich_text",
        "Full Address": "rich_text",
        "Google Maps URL": "url",
        "International Phone": "phone_number",
        "Latitude": "number",
        "Longitude": "number",
        "MedicalFacilityID": "title",
        "Monday Hours": "rich_text",
        "Name": "rich_text",
        "Phone": "phone_number",
        "Place_ID": "rich_text",
        "Saturday Hours": "rich_text",
        "Sunday Hours": "rich_text",
        "Thursday Hours": "rich_text",
        "Tuesday Hours": "rich_text",
        "Type": "select",
        "Website": "url",
        "Wednesday Hours": "rich_text",
        "address1": "rich_text",
        "address2": "rich_text",
        "address3": "rich_text",
        "borough": "rich_text",
        "city": "rich_text",
        "country": "rich_text",
        "county": "rich_text",
        "formatted_address_google": "rich_text",
        "state": "rich_text",
        "zip": "rich_text",
    }

    total = len(pages)
    yield f"Scanning Medical Facilities ({total} rows)...\n"

    counts: Dict[str, int] = {
        "updated": 0,
        "skipped_no_missing": 0,
        "skipped_no_place_id": 0,
        "errors": 0,
    }

    for idx, page in enumerate(pages, start=1):
        page_id = page.get("id") or ""
        props = page.get("properties") or {}
        missing = {name for name, ptype in fields.items() if _missing_field(props, name, ptype)}
        if not missing:
            counts["skipped_no_missing"] += 1
            continue

        place_id = _extract_place_id(props)
        if not place_id:
            counts["skipped_no_place_id"] += 1
            continue

        try:
            details = await _get_place_details(place_id)
            place = details.get("result") or details or {}
            if not place:
                raise ValueError("missing place details")

            facility_type = _extract_type(props)
            if not facility_type:
                if _is_er(place):
                    facility_type = "ER"
                elif _is_urgent_care(place):
                    facility_type = "Urgent Care"

            google_props = _build_mf_properties_from_google_place(place, facility_type or "")
            if not (google_props.get("Type", {}).get("select") or {}).get("name"):
                google_props.pop("Type", None)

            updates: Dict[str, Any] = {}
            for key, value in google_props.items():
                if key in missing:
                    updates[key] = value

            if "MedicalFacilityID" in missing:
                mf_id = await _get_next_mf_id()
                updates["MedicalFacilityID"] = {"title": [{"text": {"content": mf_id}}]}

            if not updates:
                counts["skipped_no_missing"] += 1
                continue

            await update_medical_facility_page(page_id, updates)
            counts["updated"] += 1
            yield f"Updated {idx}/{total}: page_id={page_id} fields={list(updates.keys())}\n"
        except Exception as exc:  # noqa: BLE001
            counts["errors"] += 1
            if debug_enabled():
                debug_log("MEDICAL_FACILITIES_MAINT", f"error page_id={page_id} exc={exc}")
            yield f"error: page_id={page_id} {exc}\n"

    summary = (
        f"Done. total={total} updated={counts['updated']} skipped_no_missing={counts['skipped_no_missing']} "
        f"skipped_no_place_id={counts['skipped_no_place_id']} errors={counts['errors']}\n"
    )
    yield summary
