from __future__ import annotations

import time
import re
from typing import Any, Dict, List, Tuple

from app.services.address_parser import parse_address
from app.services.logger import log_job
from app.services.notion_locations import get_locations_master_cached, load_all_production_locations
from app.services.notion_medical_facilities import fetch_and_cache_medical_facilities
from config import Config


TARGET_FIELDS = ["address1", "address2", "city", "state", "zip", "country"]


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def extract_full_address(row: Dict[str, Any]) -> str:
    """
    Extract the authoritative full address text from a master row.
    Prefers the Notion rich_text field "Full Address", falls back to normalized "address"/"full_address".
    """
    fa = row.get("Full Address")
    if isinstance(fa, list):
        plain = "".join(block.get("plain_text", "") for block in fa if isinstance(block, dict))
        full_address = plain.strip()
    else:
        full_address = ""

    if full_address:
        return full_address

    for alt_key in ("address", "full_address"):
        alt_val = row.get(alt_key)
        if isinstance(alt_val, str) and alt_val.strip():
            return alt_val.strip()

    return ""


def parse_full_address(full_address: str) -> Dict[str, Any]:
    """
    Parse a full address string using the shared address parser.
    Returns only the structured fields required for master normalization.
    """
    normalized_address = full_address or ""
    if normalized_address:
        lines = re.split(r"\r?\n", normalized_address)
        normalized_address = ", ".join([ln.strip() for ln in lines if ln.strip()])
    parsed = parse_address(normalized_address)
    return {
        "address1": parsed.get("address1") or "",
        "address2": parsed.get("address2") or "",
        "city": parsed.get("city") or "",
        "state": parsed.get("state") or "",
        "zip": parsed.get("zip") or "",
        "country": (parsed.get("country") or "").upper(),
    }


def normalize_master_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fill missing structured address fields on a master row using the full address.
    Idempotent: existing non-empty fields are preserved.
    """
    before = dict(row)
    result = dict(row)
    full_address = extract_full_address(before)
    if not full_address:
        return result

    parsed = parse_full_address(full_address)

    for field in TARGET_FIELDS:
        if is_empty(result.get(field)) and not is_empty(parsed.get(field)):
            result[field] = parsed.get(field)

    return result


def normalize_master_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize a list of master rows safely and log outcomes.
    Returns a new list; input rows are not modified.
    """
    normalized_rows: List[Dict[str, Any]] = []
    total_rows = len(rows)
    updated_rows = 0

    for row in rows:
        try:
            normalized = normalize_master_row(row)
            filled_fields = 0
            for field in TARGET_FIELDS:
                before_val = row.get(field)
                after_val = normalized.get(field)
                if is_empty(before_val) and not is_empty(after_val):
                    filled_fields += 1
            if filled_fields:
                updated_rows += 1
                log_job(
                    "address_normalization",
                    "fields_filled",
                    "success",
                    f"row_id={row.get('id') or row.get('row_id')} fields_filled={filled_fields}",
                )
            normalized_rows.append(normalized)
        except Exception as exc:  # noqa: BLE001
            log_job(
                "address_normalization",
                "parse_error",
                "error",
                f"row_id={row.get('id') or row.get('row_id')} error={exc}",
            )
            normalized_rows.append(dict(row))

    log_job(
        "address_normalization",
        "normalize_complete",
        "success",
        f"rows_scanned={total_rows} rows_updated={updated_rows}",
    )
    return normalized_rows


def apply_master_normalization(master_rows: List[Dict[str, Any]], strict: bool = True) -> Dict[str, Any]:
    """
    Determine which master rows need structured address fields filled.
    Returns a summary with updates to apply (no Notion writes performed here).
    """
    total_rows = len(master_rows)
    updates: List[Dict[str, Any]] = []

    for row in master_rows:
        full_address = extract_full_address(row)
        log_job(
            "address_normalization_debug",
            "full_address_raw",
            "success",
            f"row_id={row.get('id') or row.get('row_id')} full_address_raw={row.get('Full Address')}",
        )
        log_job(
            "address_normalization_debug",
            "full_address_extracted",
            "success",
            f"row_id={row.get('id') or row.get('row_id')} full_address_extracted='{full_address}'",
        )
        if not full_address:
            continue

        parsed = parse_full_address(full_address)
        log_job(
            "address_normalization_debug",
            "parsed_result",
            "success",
            f"row_id={row.get('id') or row.get('row_id')} parsed_result={parsed}",
        )
        log_job(
            "address_normalization_debug",
            "existing_structured_fields",
            "success",
            f"row_id={row.get('id') or row.get('row_id')} existing={{'address1': {row.get('address1')}, 'address2': {row.get('address2')}, 'city': {row.get('city')}, 'state': {row.get('state')}, 'zip': {row.get('zip')}, 'country': {row.get('country')}}}",
        )
        if not any(not is_empty(parsed.get(f)) for f in TARGET_FIELDS):
            continue  # nothing to apply

        fields_to_fill: Dict[str, Any] = {}
        for field in TARGET_FIELDS:
            raw_key = f"{field}_raw"
            existing = row.get(raw_key) if raw_key in row else row.get(field)
            candidate = parsed.get(field)
            existing_is_empty = is_empty(existing) if strict else not (existing or "").strip()
            if isinstance(existing, str) and existing.strip() == "":
                log_job(
                    "address_writeback",
                    "whitespace_detected",
                    "success",
                    f"row_id={row.get('id') or row.get('row_id')} field={field} whitespace_only",
                )
            if existing_is_empty and not is_empty(candidate):
                fields_to_fill[field] = candidate
                log_job(
                    "address_normalization_debug",
                    "needs_update",
                    "success",
                    f"row_id={row.get('id') or row.get('row_id')} field={field} empty_check=True",
                )
            else:
                log_job(
                    "address_normalization_debug",
                    "needs_update",
                    "success",
                    f"row_id={row.get('id') or row.get('row_id')} field={field} empty_check=False",
                )

        if fields_to_fill:
            updates.append({"row_id": row.get("id") or row.get("row_id"), "fields": fields_to_fill})

    rows_to_update = len(updates)
    log_job(
        "address_writeback",
        "plan",
        "success",
        f"rows_scanned={total_rows} rows_to_update={rows_to_update}",
    )

    return {
        "total_rows": total_rows,
        "rows_to_update": rows_to_update,
        "updates": updates,
    }


async def _load_rows_for_table(table_name: str) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """Resolve a supported table name to normalized rows."""
    name = table_name.strip()
    if name == "Locations Master":
        rows = await get_locations_master_cached(refresh=True)
        return "Locations Master", rows, {"raw_rows": len(rows), "filtered_rows": len(rows)}
    if name == "Medical Facilities":
        facilities = await fetch_and_cache_medical_facilities()
        rows = facilities.get("normalized", []) if isinstance(facilities, dict) else facilities
        rows = rows or []
        return "Medical Facilities", rows, {"raw_rows": len(rows), "filtered_rows": len(rows)}

    # Production-specific locations tables use the prefix before "_Locations"
    if name.endswith("_Locations"):
        abbreviation = name.replace("_Locations", "")
        prod_db = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID
        if not prod_db:
            raise RuntimeError("Missing productions master DB id for production locations normalization")
        rows = await load_all_production_locations(prod_db, refresh=True)
        raw_count = len(rows)
        abbrev = abbreviation.upper()
        filtered = [
            row
            for row in rows
            if str(row.get("production_id") or row.get("ProductionID") or "").upper() == abbrev
        ]
        fallback_used = False
        if not filtered and rows:
            filtered = rows  # fallback to all rows so preview/apply can proceed
            fallback_used = True
        return name, filtered, {
            "raw_rows": raw_count,
            "filtered_rows": len(filtered),
            "production_filter": abbrev,
            "filter_fallback_used": fallback_used,
        }

    raise ValueError(f"Unsupported table: {table_name}")


async def normalize_table(table_name: str, preview: bool = True) -> Dict[str, Any]:
    """
    Normalize address components for a given Notion table.
    Supported table names:
      - AMCL_Locations
      - TGD_Locations
      - YDEO_Locations
      - IPR_Locations
      - Locations Master
      - Medical Facilities
    """
    started = time.perf_counter()
    try:
        resolved_name, rows, load_diag = await _load_rows_for_table(table_name)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to load table {table_name}: {exc}"
        log_job("address_normalization", "normalize_load", "error", err)
        return {
            "status": "error",
            "message": err,
            "table": table_name,
            "preview": preview,
            "total_rows": 0,
            "updated": 0,
            "skipped": 0,
            "errors": [err],
            "sample_changes": [],
            "sample_existing": [],
            "diagnostics": {"raw_rows": 0, "filtered_rows": 0},
        }

    plan = apply_master_normalization(rows, strict=True)
    total_rows = plan.get("total_rows", 0)
    updates: List[Dict[str, Any]] = plan.get("updates", [])
    updated = len(updates)
    skipped = max(total_rows - updated, 0)
    errors: List[str] = []

    sample_changes = []
    for update in updates[:5]:
        sample_changes.append(
            {
                "row_id": update.get("row_id"),
                "fields": update.get("fields"),
            }
        )

    sample_existing: List[Dict[str, Any]] = []
    sample_keys: List[Dict[str, Any]] = []
    for row in rows[:5]:
        sample_existing.append(
            {
                "row_id": row.get("id") or row.get("row_id"),
                "address": row.get("address") or row.get("full_address") or row.get("Full Address"),
                "address1": row.get("address1"),
                "address2": row.get("address2"),
                "address3": row.get("address3"),
                "city": row.get("city"),
                "state": row.get("state"),
                "zip": row.get("zip"),
                "country": row.get("country"),
            }
        )
        sample_keys.append(
            {
                "row_id": row.get("id") or row.get("row_id"),
                "present_fields": sorted([k for k, v in row.items() if k in {"address1", "address2", "address3", "city", "state", "zip", "country"} and v is not None]),
            }
        )

    if preview:
        duration_ms = int((time.perf_counter() - started) * 1000)
        log_job(
            "address_normalization",
            "normalize_preview",
            "success",
            f"table={resolved_name} rows_scanned={total_rows} rows_to_update={updated} duration_ms={duration_ms}",
        )
        return {
            "status": "success",
            "message": f"Preview complete for {resolved_name}",
            "table": resolved_name,
            "preview": True,
            "total_rows": total_rows,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "sample_changes": sample_changes,
            "sample_existing": sample_existing,
            "sample_keys": sample_keys,
            "diagnostics": load_diag,
        }

    # Apply updates
    from app.services.notion_writeback import write_address_updates

    write_result = await write_address_updates(updates)
    duration_ms = int((time.perf_counter() - started) * 1000)
    log_job(
        "address_normalization",
        "normalize_apply",
        "success",
        f"table={resolved_name} rows_scanned={total_rows} rows_applied={write_result.get('successful', 0)} duration_ms={duration_ms}",
    )

    return {
        "status": "success",
        "message": f"Applied normalization for {resolved_name}",
        "table": resolved_name,
        "preview": False,
        "total_rows": total_rows,
        "updated": write_result.get("successful", 0),
        "skipped": skipped,
        "errors": write_result.get("errors", []),
        "sample_changes": sample_changes,
        "sample_existing": sample_existing,
        "sample_keys": sample_keys,
        "diagnostics": load_diag,
    }
