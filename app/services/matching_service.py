from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.services.location_status_utils import STATUS_MATCHED, STATUS_UNRESOLVED


def _eq(a: Optional[str], b: Optional[str]) -> bool:
    return (a or "").strip().lower() == (b or "").strip().lower()


def _address_key(fields: Dict[str, Any], keys: Tuple[str, ...]) -> Tuple[str, ...]:
    return tuple((fields.get(k) or "").strip().lower() for k in keys)


def find_master_candidates(
    address_fields: Dict[str, Any],
    place_id: Optional[str],
    master_cache: List[Dict[str, Any]],
    exclude_id: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Return candidate master rows and a match_reason string.
    Priority: place_id -> address key A -> B -> C.
    """
    candidates: List[Dict[str, Any]] = []
    reason = "none"
    pid = (place_id or "").strip()
    if pid:
        candidates = [row for row in master_cache if _eq(pid, row.get("place_id")) and row.get("id") != exclude_id]
        reason = "place_id"
        if candidates:
            return candidates, reason

    # Build keys
    key_a = _address_key(
        address_fields,
        ("address1", "city", "state", "zip", "country"),
    )
    key_b = _address_key(
        address_fields,
        ("address1", "city", "state", "country"),
    )
    key_c = _address_key(address_fields, ("address1", "state", "country"))

    def _match(key: Tuple[str, ...], fields: Dict[str, Any], keys: Tuple[str, ...]) -> bool:
        return key == _address_key(fields, keys)

    # A
    candidates = [row for row in master_cache if row.get("id") != exclude_id and _match(key_a, row, ("address1", "city", "state", "zip", "country"))]
    reason = "address_a"
    if candidates:
        return candidates, reason

    # B
    candidates = [row for row in master_cache if row.get("id") != exclude_id and _match(key_b, row, ("address1", "city", "state", "country"))]
    reason = "address_b"
    if candidates:
        return candidates, reason

    # C
    candidates = [row for row in master_cache if row.get("id") != exclude_id and _match(key_c, row, ("address1", "state", "country"))]
    reason = "address_c"
    if candidates:
        return candidates, reason

    return [], "none"


def match_to_master(prod_location: Dict[str, Any], master_cache: List[Dict[str, Any]], force: bool = False) -> Dict[str, Any]:
    """
    Attempt to match a production location to a master record.
    Returns dict with matched_master_id, status, notes, match_reason, candidate_count.
    """
    place_id = prod_location.get("place_id")
    exclude_id = None if force else prod_location.get("id") or prod_location.get("row_id")
    address_fields = {
        "address1": prod_location.get("address1"),
        "city": prod_location.get("city"),
        "state": prod_location.get("state"),
        "zip": prod_location.get("zip"),
        "country": prod_location.get("country"),
    }

    candidates, reason = find_master_candidates(address_fields=address_fields, place_id=place_id, master_cache=master_cache, exclude_id=exclude_id)
    candidate_count = len(candidates)

    if candidate_count == 1:
        matched_id = candidates[0].get("id")
        return {
            "matched_master_id": matched_id,
            "status": STATUS_MATCHED,
            "notes": "",
            "match_reason": reason,
            "candidate_count": candidate_count,
        }

    if candidate_count > 1:
        return {
            "matched_master_id": None,
            "status": STATUS_UNRESOLVED,
            "notes": f"Multiple candidates ({candidate_count}) via {reason}",
            "match_reason": reason,
            "candidate_count": candidate_count,
        }

    return {
        "matched_master_id": None,
        "status": STATUS_UNRESOLVED,
        "notes": "",
        "match_reason": reason,
        "candidate_count": candidate_count,
    }
