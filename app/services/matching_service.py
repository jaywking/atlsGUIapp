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
    master_cache: Dict[str, Any] | List[Dict[str, Any]],
    exclude_id: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Return candidate master rows and a match_reason string.
    Priority (canonical):
      1) place_id
      2) address hash (address1, city, state, zip, country)
      3) city/state/zip (country-aware)
    """
    # Accept either prebuilt cache dict or list of rows
    if isinstance(master_cache, dict):
        rows = master_cache.get("rows") or []
        place_index = master_cache.get("place_id_index") or {}
        hash_index = master_cache.get("canonical_hash_index") or {}
        csz_index = master_cache.get("city_state_zip_index") or {}
    else:
        rows = master_cache
        place_index = {}
        hash_index = {}
        csz_index = {}

    candidates: List[Dict[str, Any]] = []
    reason = "none"
    pid = (place_id or "").strip()
    if pid:
        if place_index:
            row = place_index.get(pid)
            if row and row.get("id") != exclude_id:
                return [row], "place_id"
        candidates = [row for row in rows if _eq(pid, row.get("place_id")) and row.get("id") != exclude_id]
        reason = "place_id"
        if candidates:
            return candidates, reason

    key_full = _address_key(address_fields, ("address1", "city", "state", "zip", "country"))
    if any(key_full) and hash_index:
        candidates = [r for r in hash_index.get(key_full, []) if r.get("id") != exclude_id]
        if candidates:
            return candidates, "address_hash"

    if not candidates:
        candidates = [
            row
            for row in rows
            if row.get("id") != exclude_id and _address_key(row, ("address1", "city", "state", "zip", "country")) == key_full
        ]
        if candidates:
            return candidates, "address_hash"

    key_city_state_zip = _address_key(address_fields, ("city", "state", "zip", "country"))
    if any(key_city_state_zip) and csz_index:
        candidates = [r for r in csz_index.get(key_city_state_zip, []) if r.get("id") != exclude_id]
        if candidates:
            return candidates, "city_state_zip"

    if not candidates:
        candidates = [
            row
            for row in rows
            if row.get("id") != exclude_id and _address_key(row, ("city", "state", "zip", "country")) == key_city_state_zip
        ]
        if candidates:
            return candidates, "city_state_zip"

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


async def stream_match_all(
    prod_locations: List[Dict[str, Any]],
    master_cache: Dict[str, Any],
    *,
    resolve_status_fn,
    update_page_fn,
    force: bool = False,
):
    """Yield progress lines while matching all production locations."""
    total = len(prod_locations)
    reviewed = matched = conflicts = unresolved = match_noop = 0
    yield f"Starting Match All... total={total}"
    for idx, record in enumerate(prod_locations, start=1):
        reviewed += 1
        yield f"Row {idx}/{total}"
        if not force and record.get("locations_master_ids"):
            match_noop += 1
            continue

        match_result = match_to_master(record, master_cache, force=force)
        candidate_count = match_result.get("candidate_count", 0)
        matched_id = match_result.get("matched_master_id")
        if candidate_count > 1:
            conflicts += 1
            continue
        if not matched_id:
            unresolved += 1
            continue

        existing_ids = record.get("locations_master_ids") or []
        existing_master_id = existing_ids[0] if existing_ids else None
        existing_status = record.get("status")
        new_status_name = resolve_status_fn(record.get("place_id"), matched=True, explicit=match_result.get("status"))

        if existing_master_id == matched_id and existing_status == new_status_name:
            match_noop += 1
            continue

        props = {
            "LocationsMasterID": {"relation": [{"id": matched_id}]},
            "Status": {"status": {"name": new_status_name}},
        }
        try:
            await update_page_fn(record.get("id") or "", props)
            matched += 1
        except Exception:
            conflicts += 1
            continue

    yield f"Done. reviewed={reviewed} matched={matched} conflicts={conflicts} unresolved={unresolved} noop={match_noop}"


async def stream_reprocess(
    prod_rows: List[Dict[str, Any]],
    master_cache: Dict[str, Any],
    resolve_status_fn,
    update_page_fn,
    force: bool = False,
):
    """Yield progress lines for reprocessing a single production's locations."""
    total = len(prod_rows)
    updated = skipped = unmatched = errors = 0
    for idx, row in enumerate(prod_rows, start=1):
        yield f"Row {idx}/{total} — processing..."
        try:
            match_result = match_to_master(row, master_cache, force=force)
            candidate_count = match_result.get("candidate_count", 0)
            matched_id = match_result.get("matched_master_id")
            if candidate_count > 1:
                unmatched += 1
                yield f"-> unmatched (multiple candidates via {match_result.get('match_reason')})"
                continue
            if not matched_id:
                unmatched += 1
                yield "-> no match found"
                continue
            props = {
                "LocationsMasterID": {"relation": [{"id": matched_id}]},
            }
            await update_page_fn(row.get("id") or "", props)
            updated += 1
            yield f"-> matched via {match_result.get('match_reason')}"
        except Exception as exc:  # noqa: BLE001
            errors += 1
            yield f"-> error: {exc}"
    yield f"Summary: updated={updated} skipped={skipped} unmatched={unmatched} errors={errors}"
