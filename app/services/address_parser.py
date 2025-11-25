from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


ZIP_RE = re.compile(r"(?P<state>[A-Za-z]{2})\s+(?P<zip>\d{5})(?:-\d{4})?$")
POSTAL_RE = re.compile(r"(?P<postal>[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d)", re.IGNORECASE)
US_STATES = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
}
CA_PROVINCES = {"ON", "QC", "NS", "NB", "MB", "BC", "PE", "SK", "AB", "NL", "NU", "YT", "NT"}


def _extract_from_components(components: Optional[List[Dict[str, Any]]]) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {
        "state": None,
        "country": None,
        "county": None,
        "borough": None,
    }
    if not components:
        return result

    for comp in components:
        types = comp.get("types") or []
        short_name = comp.get("short_name") or ""
        long_name = comp.get("long_name") or ""
        if "country" in types:
            result["country"] = (short_name or long_name or "").upper() or None
        if "administrative_area_level_1" in types:
            result["state"] = (short_name or long_name or "").upper() or None
        if "administrative_area_level_2" in types:
            name = long_name or short_name or ""
            result["county"] = name.replace("County", "").strip() or name
        if any(t.startswith("sublocality") for t in types):
            result["borough"] = long_name or short_name or None
    return result


def parse_address(full_address: str, components: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Optional[str]]:
    """
    Parse an address string into structured components (US + Canada).

    Heuristics:
    - Split by commas; use trailing segment for state/province + postal/ZIP.
    - Supports US ZIP (12345 or 12345-6789) and CA postal (A1A 1A1).
    - Extract borough/county/country if Places components are provided.
    """
    result: Dict[str, Optional[str]] = {
        "address1": None,
        "address2": None,
        "address3": None,
        "city": None,
        "state": None,
        "zip": None,
        "country": "US",
        "county": None,
        "borough": None,
    }

    comp_result = _extract_from_components(components)
    if comp_result.get("country"):
        result["country"] = comp_result["country"]
    if comp_result.get("state"):
        result["state"] = comp_result["state"]
    result["county"] = comp_result.get("county")
    result["borough"] = comp_result.get("borough")

    if not full_address:
        return result

    segments = [seg.strip() for seg in full_address.split(",") if seg.strip()]
    if len(segments) < 2:
        return result

    state_zip_segment = segments[-1]
    city_segment = segments[-2] if len(segments) >= 2 else None
    address_segments = segments[:-2] if len(segments) >= 2 else []

    postal_match = POSTAL_RE.search(state_zip_segment)
    zip_match = ZIP_RE.search(state_zip_segment)

    if zip_match:
        state = zip_match.group("state").upper()
        if state in US_STATES:
            result["state"] = state
            result["zip"] = zip_match.group("zip")
            result["country"] = result["country"] or "US"
    elif postal_match:
        result["zip"] = postal_match.group("postal").upper().replace(" ", "")
        tokens = state_zip_segment.split()
        for token in tokens:
            tok_upper = token.upper().strip(",")
            if tok_upper in CA_PROVINCES:
                result["state"] = tok_upper
                result["country"] = result["country"] or "CA"
                break
        if not result["country"]:
            result["country"] = "CA"

    if city_segment:
        result["city"] = city_segment or None

    if address_segments:
        result["address1"] = address_segments[0] or None
        if len(address_segments) > 1:
            result["address2"] = address_segments[1] or None
        if len(address_segments) > 2:
            result["address3"] = ", ".join(address_segments[2:]) or None

    return result
