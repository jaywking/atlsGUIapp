from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.address_parser import parse_address
from app.services.logger import log_job
from app.services.notion_locations import build_full_address, build_location_properties, resolve_status


def _clean_str(value: Any, upper: bool = False) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.upper() if upper else text


def _coerce_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def make_address_key(full_address: str) -> str:
    """Collapse whitespace + lowercase for duplicate detection."""
    return " ".join(full_address.lower().split()) if full_address else ""


def make_component_key(components: Dict[str, Any]) -> str:
    parts = [
        components.get("address1"),
        components.get("city"),
        components.get("state"),
        components.get("zip"),
        components.get("country"),
    ]
    normalized = [str(p).strip().lower() for p in parts if p]
    return "|".join(normalized)


def normalize_components(components: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize structured address components into canonical casing/spacing."""
    return {
        "address1": _clean_str(components.get("address1")),
        "address2": _clean_str(components.get("address2")),
        "address3": _clean_str(components.get("address3")),
        "city": _clean_str(components.get("city")),
        "state": _clean_str(components.get("state"), upper=True),
        "zip": _clean_str(components.get("zip")),
        "country": _clean_str(components.get("country"), upper=True) or "US",
        "county": _clean_str(components.get("county")),
        "borough": _clean_str(components.get("borough")),
    }


def normalize_ingest_record(
    row: Dict[str, Any],
    *,
    production_id: str | None = None,
    log_category: str = "ingest_normalization",
    log: bool = True,
) -> Dict[str, Any]:
    """
    Canonical normalization pipeline for incoming location/facility rows.

    Returns dict with:
      - components (address1/address2/address3/city/state/zip/country/county/borough)
      - full_address (formatted string)
      - place_id
      - place_name
      - latitude / longitude (if present)
      - production_id
      - address_key / components_key (for dedup/indexing)
    """
    raw_full = (
        row.get("full_address")
        or row.get("Full Address")
        or row.get("address")
        or row.get("Address")
        or ""
    )
    parsed = parse_address(str(raw_full))
    components = normalize_components(
        {
            "address1": row.get("address1") or row.get("Address 1") or parsed.get("address1"),
            "address2": row.get("address2") or row.get("Address 2") or parsed.get("address2"),
            "address3": row.get("address3") or row.get("Address 3") or parsed.get("address3"),
            "city": row.get("city") or row.get("City") or parsed.get("city"),
            "state": row.get("state") or row.get("State") or row.get("state_province") or parsed.get("state"),
            "zip": row.get("zip") or row.get("ZIP") or row.get("postal") or parsed.get("zip"),
            "country": row.get("country") or row.get("Country") or parsed.get("country"),
            "county": row.get("county") or parsed.get("county"),
            "borough": row.get("borough") or parsed.get("borough"),
        }
    )
    formatted_full = build_full_address(components)
    if not formatted_full and raw_full:
        formatted_full = str(raw_full).strip()

    normalized: Dict[str, Any] = {
        "components": components,
        "full_address": formatted_full,
        "raw_address": str(raw_full).strip(),
        "place_id": row.get("place_id") or row.get("Place_ID") or row.get("placeId"),
        "place_name": row.get("place_name") or row.get("name") or row.get("Location Name"),
        "latitude": _coerce_float(row.get("latitude") or row.get("lat")),
        "longitude": _coerce_float(row.get("longitude") or row.get("lng")),
        "production_id": production_id or row.get("production_id") or "",
    }
    normalized["address_key"] = make_address_key(normalized["full_address"])
    normalized["components_key"] = make_component_key(components)

    if log:
        log_job(
            log_category,
            "normalized",
            "success",
            f"production_id={normalized['production_id'] or 'master'} place_id={normalized.get('place_id') or 'none'}",
        )
    return normalized


def build_location_payload(
    normalized: Dict[str, Any],
    *,
    status: Optional[str] = None,
    matched_master_id: Optional[str] = None,
    production_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build Notion properties for Locations (master or production) from normalized data."""
    resolved_status = resolve_status(
        place_id=normalized.get("place_id"),
        matched=bool(matched_master_id),
        explicit=status,
    )
    return build_location_properties(
        components=normalized.get("components", {}),
        production_id=production_id or normalized.get("production_id") or "",
        place_id=normalized.get("place_id"),
        place_name=normalized.get("place_name"),
        latitude=normalized.get("latitude"),
        longitude=normalized.get("longitude"),
        status=resolved_status,
        matched=bool(matched_master_id),
        matched_master_id=matched_master_id,
    )


def build_facility_properties(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """Build Notion-ready properties for the Medical Facilities DB."""
    components = normalized.get("components", {})
    full_address = normalized.get("full_address") or ""

    def _rt(value: str) -> Dict[str, Any]:
        return {"rich_text": [{"text": {"content": value}}]}

    props: Dict[str, Any] = {
        "Address": _rt(full_address),
        "Address 1": _rt(components.get("address1") or ""),
        "Address 2": _rt(components.get("address2") or ""),
        "Address 3": _rt(components.get("address3") or ""),
        "City": _rt(components.get("city") or ""),
        "State / Province": _rt(components.get("state") or ""),
        "ZIP / Postal Code": _rt(components.get("zip") or ""),
        "Country": _rt(components.get("country") or ""),
        "County": _rt(components.get("county") or ""),
        "Borough": _rt(components.get("borough") or ""),
    }
    if normalized.get("place_id"):
        props["Place_ID"] = _rt(str(normalized["place_id"]))
    if normalized.get("place_name"):
        props["Name"] = _rt(str(normalized["place_name"]))
    return props
