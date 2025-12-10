from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.services.notion_locations import get_locations_master_cached


def _address_key(fields: Dict[str, Any], keys: Tuple[str, ...]) -> Tuple[str, ...]:
    return tuple((fields.get(k) or "").strip().lower() for k in keys)


def _canonical_hash(row: Dict[str, Any]) -> Tuple[str, ...]:
    return _address_key(row, ("address1", "city", "state", "zip", "country"))


def _city_state_zip(row: Dict[str, Any]) -> Tuple[str, ...]:
    return _address_key(row, ("city", "state", "zip", "country"))


async def load_master_cache(refresh: bool = False) -> Dict[str, Any]:
    """
    Load canonical Locations Master rows and build matching indexes.
    Returns {
      "rows": [...],
      "place_id_index": {place_id: row},
      "canonical_hash_index": {hash: [rows]},
      "city_state_zip_index": {hash: [rows]},
    }
    """
    rows = await get_locations_master_cached(refresh=refresh)
    place_id_index: Dict[str, Dict[str, Any]] = {}
    canonical_hash_index: Dict[Tuple[str, ...], List[Dict[str, Any]]] = {}
    city_state_zip_index: Dict[Tuple[str, ...], List[Dict[str, Any]]] = {}

    for row in rows:
        pid = (row.get("place_id") or "").strip()
        if pid:
            place_id_index[pid] = row

        h = _canonical_hash(row)
        if any(h):
            canonical_hash_index.setdefault(h, []).append(row)

        csz = _city_state_zip(row)
        if any(csz):
            city_state_zip_index.setdefault(csz, []).append(row)

    return {
        "rows": rows,
        "place_id_index": place_id_index,
        "canonical_hash_index": canonical_hash_index,
        "city_state_zip_index": city_state_zip_index,
    }
