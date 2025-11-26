from __future__ import annotations

import math
from typing import Any, Dict, List


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _clean(val: Any) -> str:
    return str(val or "").strip().lower()


def _address_mismatch(prod: Dict[str, Any], master: Dict[str, Any]) -> bool:
    fields = ["address1", "city", "state", "zip", "country"]
    for f in fields:
        if _clean(prod.get(f)) != _clean(master.get(f)):
            return True
    return False


def _place_id_mismatch(prod: Dict[str, Any], master: Dict[str, Any]) -> bool:
    p = _clean(prod.get("place_id"))
    m = _clean(master.get("place_id"))
    if p and m:
        return p != m
    return False


def _coord_status(prod: Dict[str, Any], master: Dict[str, Any]) -> str:
    try:
        plat = float(prod.get("latitude"))
        plon = float(prod.get("longitude"))
        mlat = float(master.get("latitude"))
        mlon = float(master.get("longitude"))
    except Exception:
        return "unknown"
    distance = _haversine_meters(plat, plon, mlat, mlon)
    if distance <= 30:
        return "ok"
    if distance <= 200:
        return "suspect"
    return "mismatch"


def validate_links(prod_locations: List[Dict[str, Any]], master_cache: List[Dict[str, Any]]) -> Dict[str, Any]:
    master_by_id = {m.get("id"): m for m in master_cache}
    reviewed = 0
    invalid_items: List[Dict[str, Any]] = []

    for prod in prod_locations:
        reviewed += 1
        master_ids = prod.get("locations_master_ids") or []
        if not master_ids:
            continue
        master_id = master_ids[0]
        master = master_by_id.get(master_id)
        if not master:
            invalid_items.append(
                {
                    "prod_loc_id": prod.get("prod_loc_id") or "",
                    "production_id": prod.get("production_id") or "",
                    "master_id": master_id,
                    "place_id_mismatch": True,
                    "address_mismatch": True,
                    "coordinate_mismatch": "unknown",
                    "detail": "Master record missing",
                }
            )
            continue

        place_mismatch = _place_id_mismatch(prod, master)
        address_mismatch = _address_mismatch(prod, master)
        coord_state = _coord_status(prod, master)
        is_invalid = place_mismatch or address_mismatch or coord_state == "mismatch"
        if is_invalid:
            invalid_items.append(
                {
                    "prod_loc_id": prod.get("prod_loc_id") or "",
                    "production_id": prod.get("production_id") or "",
                    "master_id": master_id,
                    "place_id_mismatch": place_mismatch,
                    "address_mismatch": address_mismatch,
                    "coordinate_mismatch": coord_state,
                    "detail": "Validation failed",
                }
            )

    valid = reviewed - len(invalid_items)
    return {
        "status": "success",
        "reviewed": reviewed,
        "valid": valid,
        "invalid": len(invalid_items),
        "invalid_items": invalid_items,
    }
