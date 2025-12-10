from __future__ import annotations

import re
from typing import Any, Dict, Optional

import httpx

from app.services.logger import log_job
from app.services.notion_locations import build_location_properties, resolve_status
from config import Config

GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
NYC_BOROUGHS = {"MANHATTAN", "BROOKLYN", "QUEENS", "BRONX", "STATEN ISLAND", "NEW YORK"}


def _clean_str(value: Any, upper: bool = False) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.upper() if upper else text


def _title_case(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value.title() if value else None


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


def _normalize_zip(zip_code: Optional[str], country: str) -> Optional[str]:
    if not zip_code:
        return None
    zip_str = str(zip_code).strip()
    if country == "US":
        match = re.search(r"\d{5}", zip_str)
        return match.group(0) if match else None
    return zip_str


def _normalize_country(country: Optional[str], google_short: Optional[str] = None) -> str:
    value = (country or google_short or "US").strip().upper()
    if len(value) > 2:
        value = value[:2]
    return value or "US"


def _normalize_state(state: Optional[str]) -> Optional[str]:
    if not state:
        return None
    return str(state).strip().upper()[:2]


def _extract_component(components: list[dict[str, Any]], type_key: str, name_key: str = "long_name") -> Optional[str]:
    for comp in components:
        if type_key in comp.get("types", []):
            return comp.get(name_key) or None
    return None


def _extract_county(components: list[dict[str, Any]]) -> Optional[str]:
    county = _extract_component(components, "administrative_area_level_2")
    if not county:
        return None
    county_clean = county.replace("County", "").strip()
    return county_clean or None


def _extract_borough(components: list[dict[str, Any]], city: Optional[str]) -> Optional[str]:
    for comp in components:
        if "sublocality_level_1" in comp.get("types", []):
            candidate = (comp.get("long_name") or "").strip().upper()
            if candidate in NYC_BOROUGHS:
                return candidate.title()
    city_upper = (city or "").strip().upper()
    if city_upper in NYC_BOROUGHS:
        return city_upper.title()
    return None


def _format_address1(street_number: Optional[str], route: Optional[str]) -> Optional[str]:
    parts = [p for p in [street_number, route] if p]
    joined = " ".join(parts).strip()
    return joined or None


def _build_full_address_atls(components: Dict[str, Optional[str]]) -> str:
    address1 = components.get("address1") or ""
    city = components.get("city") or ""
    state = components.get("state") or ""
    zip_code = components.get("zip") or ""
    country = (components.get("country") or "US").upper()
    core = f"{address1}, {city}, {state} {zip_code}".strip().replace("  ", " ")
    if country and country != "US":
        return f"{core}, {country}".strip().replace("  ", " ")
    return core.strip().replace("  ", " ")


def _google_lookup(full_address: str, place_id: Optional[str]) -> Dict[str, Any]:
    api_key = Config.GOOGLE_MAPS_API_KEY
    if not api_key:
        raise ValueError("Google Maps API key missing for geocode lookup")
    params = {"key": api_key}
    if place_id:
        params["place_id"] = place_id
    else:
        params["address"] = full_address
    response = httpx.get(GOOGLE_GEOCODE_URL, params=params, timeout=10.0)
    response.raise_for_status()
    data = response.json()
    status = data.get("status")
    results = data.get("results") or []
    if status != "OK" or not results:
        raise ValueError(f"Google geocode failed: {status or 'unknown'}")
    return results[0]


def _components_from_google(result: Dict[str, Any]) -> Dict[str, Any]:
    comps = result.get("address_components") or []
    street_number = _extract_component(comps, "street_number", "long_name")
    route = _extract_component(comps, "route", "short_name") or _extract_component(comps, "route", "long_name")
    address1 = _format_address1(street_number, route) or _extract_component(comps, "premise", "long_name")
    address2 = _extract_component(comps, "subpremise", "long_name") or _extract_component(comps, "floor", "long_name")
    city = _extract_component(comps, "locality", "long_name") or _extract_component(comps, "postal_town", "long_name") or _extract_component(comps, "sublocality", "long_name")
    state = _normalize_state(_extract_component(comps, "administrative_area_level_1", "short_name"))
    country = _normalize_country(_extract_component(comps, "country", "short_name"))
    zip_code = _normalize_zip(_extract_component(comps, "postal_code", "long_name"), country)
    county = _extract_county(comps)
    borough = _extract_borough(comps, city)
    return {
        "address1": address1,
        "address2": address2,
        "address3": None,
        "city": _title_case(city),
        "state": state,
        "zip": zip_code,
        "country": country,
        "county": county,
        "borough": borough,
    }


def normalize_components(components: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize structured address components into canonical casing/spacing (ATLS rules)."""
    country = _normalize_country(components.get("country"))
    normalized = {
        "address1": _clean_str(components.get("address1")),
        "address2": _clean_str(components.get("address2")),
        "address3": _clean_str(components.get("address3")),
        "city": _title_case(components.get("city")),
        "state": _normalize_state(components.get("state")),
        "zip": _normalize_zip(components.get("zip"), country),
        "country": country,
        "county": _clean_str(components.get("county")),
        "borough": _clean_str(components.get("borough")),
    }
    return normalized


def _google_geometry(result: Dict[str, Any]) -> tuple[Optional[float], Optional[float]]:
    loc = (result.get("geometry") or {}).get("location") or {}
    return _coerce_float(loc.get("lat")), _coerce_float(loc.get("lng"))


def normalize_ingest_record(
    row: Dict[str, Any],
    *,
    production_id: str | None = None,
    log_category: str = "ingest_normalization",
    log: bool = True,
) -> Dict[str, Any]:
    """
    Canonical normalization pipeline (v0.9.0).

    Rules:
      - Require Full Address or structured fields.
      - If Full Address provided: perform fresh Google lookup, overwrite all structured fields, apply ATLS format, store formatted_address_google.
      - If Place_ID provided without Full Address: attempt Google lookup by place_id to refresh structured fields.
      - If only structured fields provided: build Full Address using ATLS format.
    """
    full_address_input = (
        row.get("full_address")
        or row.get("Full Address")
        or row.get("address")
        or row.get("Address")
        or ""
    )
    place_id_input = row.get("place_id") or row.get("Place_ID") or row.get("placeId")

    has_structured = any(
        row.get(k)
        for k in (
            "address1",
            "address2",
            "address3",
            "city",
            "state",
            "zip",
            "country",
            "county",
            "borough",
        )
    )

    if not full_address_input and not has_structured:
        raise ValueError("Address incomplete: Full Address or structured fields required.")

    google_result: Dict[str, Any] | None = None
    formatted_address_google: Optional[str] = None
    components: Dict[str, Any] = {}
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = place_id_input

    # Full Address path (authoritative)
    if full_address_input:
        google_result = _google_lookup(str(full_address_input), place_id_input)
        components = _components_from_google(google_result)
        formatted_address_google = google_result.get("formatted_address")
        latitude, longitude = _google_geometry(google_result)
        place_id = place_id or google_result.get("place_id")
    # Place_ID refresh path
    elif place_id_input:
        try:
            google_result = _google_lookup("", place_id_input)
            components = _components_from_google(google_result)
            formatted_address_google = google_result.get("formatted_address")
            latitude, longitude = _google_geometry(google_result)
            place_id = place_id or google_result.get("place_id")
        except Exception:
            components = normalize_components(row)
    else:
        components = normalize_components(row)

    if not components.get("address1") and has_structured:
        components = normalize_components(row)

    normalized_components = normalize_components(components)

    if not normalized_components.get("address1") or not normalized_components.get("city") or not normalized_components.get("state"):
        raise ValueError("Address incomplete: structured fields missing required components.")

    full_address = _build_full_address_atls(normalized_components)

    normalized: Dict[str, Any] = {
        "components": normalized_components,
        "full_address": full_address,
        "formatted_address_google": formatted_address_google,
        "place_id": place_id,
        "place_name": row.get("place_name") or row.get("name") or row.get("Location Name"),
        "latitude": latitude if latitude is not None else _coerce_float(row.get("latitude") or row.get("lat")),
        "longitude": longitude if longitude is not None else _coerce_float(row.get("longitude") or row.get("lng")),
        "production_id": production_id or row.get("production_id") or "",
    }
    normalized["address_key"] = make_address_key(normalized["full_address"])
    normalized["components_key"] = make_component_key(normalized_components)

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
        formatted_address_google=normalized.get("formatted_address_google"),
    )


def build_facility_properties(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """Build Notion-ready properties for the Medical Facilities DB."""
    components = normalized.get("components", {})
    full_address = normalized.get("full_address") or ""

    def _rt(value: str) -> Dict[str, Any]:
        return {"rich_text": [{"text": {"content": value}}]}

    props: Dict[str, Any] = {
        "Full Address": _rt(full_address),
        "address1": _rt(components.get("address1") or ""),
        "address2": _rt(components.get("address2") or ""),
        "address3": _rt(components.get("address3") or ""),
        "city": _rt(components.get("city") or ""),
        "state": _rt(components.get("state") or ""),
        "zip": _rt(components.get("zip") or ""),
        "country": _rt(components.get("country") or ""),
        "county": _rt(components.get("county") or ""),
        "borough": _rt(components.get("borough") or ""),
    }
    if normalized.get("place_id"):
        props["Place_ID"] = _rt(str(normalized["place_id"]))
    if normalized.get("place_name"):
        props["place_name"] = _rt(str(normalized["place_name"]))
    if normalized.get("formatted_address_google"):
        props["formatted_address_google"] = _rt(str(normalized["formatted_address_google"]))
    if normalized.get("latitude") is not None:
        props["Latitude"] = {"number": normalized.get("latitude")}
    if normalized.get("longitude") is not None:
        props["Longitude"] = {"number": normalized.get("longitude")}
    return props
