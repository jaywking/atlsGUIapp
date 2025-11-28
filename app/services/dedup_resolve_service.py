from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from app.services.address_normalizer import is_empty
from app.services.logger import log_job


STRUCTURED_FIELDS = ["address1", "address2", "address3", "city", "state", "zip", "country", "latitude", "longitude", "place_id"]
NAME_FIELDS = ["name"]


def _score_row(row: Dict[str, Any]) -> float:
    score = 0.0
    place_id = (row.get("place_id") or "").strip()
    if place_id and not place_id.lower().startswith("temp"):
        score += 100
    name_len = len((row.get("name") or "").strip())
    score += min(name_len, 100) / 10
    filled = sum(1 for f in STRUCTURED_FIELDS if not is_empty(row.get(f)))
    score += filled * 2
    ts = row.get("last_edited_time") or row.get("last_edited")
    if ts:
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            score += dt.timestamp() / 1e10  # keep small influence
        except Exception:
            pass
    return score


def _choose_primary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return max(rows, key=_score_row)


def _merge_fields(primary: Dict[str, Any], duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
    updates: Dict[str, Any] = {}
    for field in STRUCTURED_FIELDS:
        if not is_empty(primary.get(field)):
            continue
        for dup in duplicates:
            if not is_empty(dup.get(field)):
                updates[field] = dup.get(field)
                log_job("dedup_resolve_debug", "field_fill", "success", f"field={field} source_row={dup.get('id') or dup.get('row_id')}")
                break
    return updates


def build_merge_plan(primary_row: Dict[str, Any], duplicate_rows: List[Dict[str, Any]], production_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a merge plan for a dedup group.
    """
    if not primary_row:
        raise ValueError("primary_row is required")
    if not duplicate_rows:
        raise ValueError("duplicate_rows cannot be empty")

    primary_id = primary_row.get("id") or primary_row.get("row_id")
    dup_ids = [r.get("id") or r.get("row_id") for r in duplicate_rows]

    field_updates = _merge_fields(primary_row, duplicate_rows)

    prod_loc_updates: List[Dict[str, Any]] = []
    for prod in production_rows:
        master_ids = prod.get("locations_master_ids") or []
        if not master_ids:
            continue
        for dup_id in dup_ids:
            if dup_id in master_ids:
                prod_loc_updates.append(
                    {
                        "prod_loc_id": prod.get("id") or prod.get("row_id"),
                        "production_id": prod.get("production_id") or "",
                        "old_master_id": dup_id,
                        "new_master_id": primary_id,
                    }
                )
                log_job(
                    "dedup_resolve_debug",
                    "prod_pointer_update",
                    "success",
                    f"prod_loc_id={prod.get('id') or prod.get('row_id')} old_master_id={dup_id} new_master_id={primary_id}",
                )
                break

    delete_master_ids = dup_ids

    return {
        "primary": primary_row,
        "to_merge": duplicate_rows,
        "field_updates": field_updates,
        "prod_loc_updates": prod_loc_updates,
        "delete_master_ids": delete_master_ids,
    }


def choose_primary_with_heuristics(rows: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if not rows or len(rows) < 2:
        raise ValueError("At least two rows required to choose primary")
    primary = _choose_primary(rows)
    duplicates = [r for r in rows if (r.get("id") or r.get("row_id")) != (primary.get("id") or primary.get("row_id"))]
    log_job(
        "dedup_resolve",
        "primary_selected",
        "success",
        f"primary_id={primary.get('id') or primary.get('row_id')} duplicates={len(duplicates)}",
    )
    return primary, duplicates
