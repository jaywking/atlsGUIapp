from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.services.ingestion_normalizer import normalize_ingest_record
from app.services.logger import log_job
from app.services.notion_locations import (
    fetch_database_title,
    fetch_production_locations,
    get_locations_master_cached,
    list_production_location_databases,
    update_location_page,
)
from app.services.notion_medical_facilities import (
    fetch_and_cache_medical_facilities,
    update_medical_facility_page,
)
from config import Config

logging.getLogger("httpx").setLevel(logging.WARNING)


def _rt(value: str) -> Dict[str, Any]:
    return {"rich_text": [{"text": {"content": value}}]}


def _num(value: float | None) -> Dict[str, Any]:
    return {"number": value}


def _clean(val: Any) -> str:
    return str(val or "").strip()


def _eq(a: Any, b: Any) -> bool:
    return _clean(a).lower() == _clean(b).lower()


def _eq_num(a: Any, b: Any) -> bool:
    try:
        return float(a) == float(b)
    except Exception:
        return False


def _print_full_diffs(row_id: str, diffs: Dict[str, Dict[str, Any]]) -> None:
    """
    Print a user-friendly diff summary for a single row.
    diffs: { field_name: {"before": old_val, "after": new_val}, ... }
    """
    print(f"\nRow: {row_id}")
    for field, change in diffs.items():
        before = change.get("before")
        after = change.get("after")
        print(f"  {field}: {before!r} → {after!r}")


def _write_patch_log(db_label: str, row_id: str, props: Dict[str, Any]) -> None:
    try:
        log_path = Path("logs/address_repair_patches.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "database": db_label,
            "row_id": row_id,
            "properties": props,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"{entry}\n")
    except Exception:
        pass


def _fallback_parse_components(full_address: str) -> Dict[str, Optional[str]]:
    """
    Fallback parser for structured address components from a multi-line Full Address.
    Expected formats:
        "123 Main St\nCity, ST 12345"
        "Building Name\n123 Main St\nCity, ST 12345"

    Returns canonical keys:
        address1, address2, address3,
        city, state, zip,
        country=None, county=None, borough=None
    """
    if not full_address:
        return {}

    lines = [line.strip() for line in full_address.split("\n") if line.strip()]
    if not lines:
        return {}

    address1 = lines[0]
    address2 = None
    address3 = None

    last = lines[-1]
    city = state = zip_code = None
    if "," in last:
        city_part, rest = last.split(",", 1)
        city = city_part.strip()
        parts = rest.strip().split()
        if len(parts) >= 2:
            state = parts[0]
            zip_code = parts[1]

    if len(lines) == 3:
        address2 = lines[1]
    elif len(lines) > 3:
        address2 = lines[1]

    return {
        "address1": address1,
        "address2": address2,
        "address3": address3,
        "city": city,
        "state": state,
        "zip": zip_code,
        "country": None,
        "county": None,
        "borough": None,
    }


async def _process_rows(
    rows: Iterable[Dict[str, Any]],
    build_updates_fn,
    apply_fn,
    dry_run: bool,
    category: str,
    production_id: str = "",
    log_detail: bool = True,
    collect_diffs: bool = False,
    db_label: str = "unknown",
) -> Dict[str, int]:
    stats = {"processed": 0, "updated": 0, "skipped": 0, "errors": 0}
    diffs: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def _extract_new_value(value: Any) -> Any:
        if isinstance(value, dict):
            if "rich_text" in value:
                arr = value.get("rich_text") or []
                return " ".join([a.get("text", {}).get("content", "") for a in arr if isinstance(a, dict)])
            if "number" in value:
                return value.get("number")
        return value

    for row in rows:
        stats["processed"] += 1
        try:
            normalized = normalize_ingest_record(row, production_id=production_id or row.get("production_id") or "", log_category=category)
            updates = build_updates_fn(row, normalized)
        except Exception as exc:  # noqa: BLE001
            stats["errors"] += 1
            if log_detail:
                log_job(category, "normalize_error", "error", f"row_id={row.get('id')} error={exc}")
            continue

        if not updates:
            stats["skipped"] += 1
            continue

        stats["updated"] += 1
        if collect_diffs:
            row_id = row.get("id") or row.get("row_id") or "<unknown>"
            row_diffs: Dict[str, Dict[str, Any]] = {}
            for prop, val in updates.items():
                new_val = _clean(_extract_new_value(val))
                old_val = _clean(row.get(prop))
                if new_val and not _eq(old_val, new_val):
                    row_diffs[prop] = {"before": old_val, "after": new_val}
            if row_diffs:
                diffs[row_id] = row_diffs

        if dry_run or not apply_fn:
            if log_detail:
                log_job(category, "dry_run", "success", f"row_id={row.get('id')} fields={list(updates.keys())}")
            continue

        try:
            _write_patch_log(db_label, row.get("id") or "", updates)
            await apply_fn(row.get("id") or "", updates)
            if log_detail:
                log_job(category, "update", "success", f"row_id={row.get('id')} fields={list(updates.keys())}")
        except Exception as exc:  # noqa: BLE001
            stats["errors"] += 1
            if log_detail:
                log_job(category, "update", "error", f"row_id={row.get('id')} error={exc}")
    if collect_diffs and diffs:
        stats["diffs"] = diffs  # type: ignore[assignment]
    return stats


def _build_location_updates(row: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
    components = normalized.get("components") or {}
    full_address = _clean(normalized.get("full_address"))

    # If components missing or any key is empty, derive/merge from Full Address
    if full_address and (
        not components
        or all(not components.get(k) for k in ("address1", "city", "state", "zip"))
    ):
        fallback = _fallback_parse_components(full_address)
        merged: Dict[str, Any] = dict(components)
        for key, value in fallback.items():
            if not merged.get(key):
                merged[key] = value
        components = merged

    props: Dict[str, Any] = {}
    field_map = {
        "address1": "address1",
        "address2": "address2",
        "address3": "address3",
        "city": "city",
        "state": "state",
        "zip": "zip",
        "country": "country",
        "county": "county",
        "borough": "borough",
    }

    for key, notion_key in field_map.items():
        new_val = _clean(components.get(key))
        # Prefer raw value pulled directly from Notion before any local parsing
        old_raw = row.get(f"{key}_raw")
        if old_raw is None:
            old_raw = row.get(key)
        if isinstance(old_raw, list):
            old_val = " ".join([_clean(part.get("plain_text") or part.get("text", {}).get("content") or "") for part in old_raw if isinstance(part, dict)])
        else:
            old_val = _clean(old_raw)

        if new_val and (not old_val or not _eq(old_val, new_val)):
            props[notion_key] = _rt(new_val)

    full_address = _clean(normalized.get("full_address"))
    old_full = _clean(row.get("Full Address") or row.get("full_address") or row.get("address"))
    if full_address and not _eq(old_full, full_address):
        props["Full Address"] = _rt(full_address)

    place_id_new = _clean(normalized.get("place_id"))
    place_id_old = _clean(row.get("Place_ID") or row.get("place_id"))
    if place_id_new and not _eq(place_id_old, place_id_new):
        props["Place_ID"] = _rt(place_id_new)

    # Ensure structured fields accompany a new Full Address
    if "Full Address" in props:
        fallback_components = _fallback_parse_components(full_address)
        for key, notion_key in field_map.items():
            new_val = _clean(fallback_components.get(key))
            if not new_val:
                continue
            if notion_key not in props:
                props[notion_key] = _rt(new_val)

    lat_new = normalized.get("latitude")
    lon_new = normalized.get("longitude")
    lat_old = row.get("latitude")
    lon_old = row.get("longitude")
    if lat_new is not None and not _eq_num(lat_new, lat_old):
        props["Latitude"] = _num(lat_new)
    if lon_new is not None and not _eq_num(lon_new, lon_old):
        props["Longitude"] = _num(lon_new)

    return props


def _build_facility_updates(row: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
    components = normalized.get("components", {})
    props: Dict[str, Any] = {}
    field_map = {
        "address1": "address1",
        "address2": "address2",
        "address3": "address3",
        "city": "city",
        "state": "state",
        "zip": "zip",
        "country": "country",
        "county": "county",
        "borough": "borough",
    }

    for key, notion_key in field_map.items():
        new_val = _clean(components.get(key))
        old_val = _clean(row.get(key))
        if new_val and not _eq(old_val, new_val):
            props[notion_key] = _rt(new_val)

    full_address = _clean(normalized.get("full_address"))
    old_full = _clean(row.get("Full Address"))
    if full_address and not _eq(old_full, full_address):
        props["Full Address"] = _rt(full_address)

    place_id_new = _clean(normalized.get("place_id"))
    place_id_old = _clean(row.get("Place_ID"))
    if place_id_new and not _eq(place_id_old, place_id_new):
        props["Place_ID"] = _rt(place_id_new)

    return props


async def _repair_master_rows(dry_run: bool) -> Dict[str, Any]:
    rows = await get_locations_master_cached(refresh=True)
    return await _process_rows(rows, _build_location_updates, update_location_page, dry_run, category="address_repair", db_label="Locations Master")


async def _repair_production_rows(dry_run: bool) -> Dict[str, Any]:
    prod_master = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    if not prod_master:
        raise RuntimeError("Missing productions master database id")

    # Repair all production DBs in one pass (non-interactive bulk path)
    entries = await discover_all_repairable_dbs(include_master=False, include_productions=True, include_facilities=False)
    stats = {"processed": 0, "updated": 0, "skipped": 0, "errors": 0}
    for entry in entries:
        db_stats = await _repair_single_production(entry, dry_run=dry_run)
        for k, v in db_stats.items():
            stats[k] = stats.get(k, 0) + v
    return stats


async def _repair_facility_rows(dry_run: bool) -> Dict[str, Any]:
    rows = await fetch_and_cache_medical_facilities()
    if isinstance(rows, dict):
        rows = rows.get("normalized", [])
    return await _process_rows(
        rows,
        _build_facility_updates,
        update_medical_facility_page,
        dry_run,
        category="address_repair",
    )


async def _repair_single_production(entry: Dict[str, Any], dry_run: bool, log_detail: bool = True) -> Dict[str, Any]:
    rows = await fetch_production_locations(entry["id"], production_id=entry.get("name"))
    return await _process_rows(
        rows,
        _build_location_updates,
        update_location_page,
        dry_run,
        category="address_repair",
        production_id=entry.get("name") or "",
        log_detail=log_detail,
        db_label=entry.get("name") or entry.get("id") or "production",
    )


async def _repair_facilities(dry_run: bool, log_detail: bool = True) -> Dict[str, Any]:
    rows = await fetch_and_cache_medical_facilities()
    if isinstance(rows, dict):
        rows = rows.get("normalized", [])
    return await _process_rows(
        rows,
        _build_facility_updates,
        update_medical_facility_page,
        dry_run,
        category="address_repair",
        log_detail=log_detail,
        db_label="Medical Facilities",
    )


async def discover_all_repairable_dbs(
    include_master: bool = True,
    include_productions: bool = True,
    include_facilities: bool = True,
) -> List[Dict[str, Any]]:
    dbs: List[Dict[str, Any]] = []
    if include_master and Config.LOCATIONS_MASTER_DB:
        dbs.append({"name": "Locations Master", "id": Config.LOCATIONS_MASTER_DB, "type": "master"})

    if include_productions:
        prod_master = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
        if prod_master:
            records = await list_production_location_databases(prod_master)
            for rec in records:
                display_name = rec.get("production_id") or rec.get("name") or rec.get("locations_db_id")
                dbs.append(
                    {
                        "name": display_name,
                        "id": rec.get("locations_db_id"),
                        "type": "production",
                    }
                )
    if include_facilities and Config.MEDICAL_FACILITIES_DB:
        dbs.append({"name": "Medical Facilities", "id": Config.MEDICAL_FACILITIES_DB, "type": "facility"})

    # Enrich names with actual DB titles (best-effort, in parallel)
    title_tasks: List[asyncio.Task] = []
    title_indices: List[int] = []
    for i, entry in enumerate(dbs):
        if entry.get("id"):
            title_indices.append(i)
            title_tasks.append(asyncio.create_task(fetch_database_title(entry["id"])))
    if title_tasks:
        resolved = await asyncio.gather(*title_tasks, return_exceptions=True)
        for idx, result in zip(title_indices, resolved):
            if isinstance(result, Exception):
                continue
            if result:
                dbs[idx]["name"] = result

    return [db for db in dbs if db.get("id")]


async def preview_db_repairs(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Return total rows and rows needing repair for a single DB entry, including fetched rows for reuse."""
    name = entry.get("name") or entry.get("id") or "Unknown"
    print(f"Fetching {name}…")
    if entry["type"] == "master":
        rows = await get_locations_master_cached(refresh=True)
        stats = await _process_rows(rows, _build_location_updates, None, True, category="address_repair", log_detail=False)
        print(f"Preview: {name} → {stats.get('updated', 0)} need repair out of {len(rows)}")
        return {"entry": entry, "total": len(rows), "needs": stats.get("updated", 0), "rows": rows}
    if entry["type"] == "production":
        rows = await fetch_production_locations(entry["id"], production_id=entry.get("name"))
        stats = await _process_rows(
            rows,
            _build_location_updates,
            None,
            True,
            category="address_repair",
            production_id=entry.get("name") or "",
            log_detail=False,
        )
        print(f"Preview: {name} → {stats.get('updated', 0)} need repair out of {len(rows)}")
        return {"entry": entry, "total": len(rows), "needs": stats.get("updated", 0), "rows": rows}
    if entry["type"] == "facility":
        rows = await fetch_and_cache_medical_facilities()
        if isinstance(rows, dict):
            rows = rows.get("normalized", [])
        stats = await _process_rows(rows, _build_facility_updates, None, True, category="address_repair", log_detail=False)
        print(f"Preview: {name} → {stats.get('updated', 0)} need repair out of {len(rows)}")
        return {"entry": entry, "total": len(rows), "needs": stats.get("updated", 0), "rows": rows}
    return {"entry": entry, "total": 0, "needs": 0, "rows": []}


async def run_repair(target: str, dry_run: bool = False) -> Dict[str, Any]:
    target = target.lower()
    targets: Iterable[str]
    if target == "all":
        targets = ("master", "productions", "facilities")
    else:
        targets = (target,)

    summary: Dict[str, Any] = {}
    for t in targets:
        if t == "master":
            log_job("address_repair", "start", "start", f"target=master dry_run={dry_run}")
            summary["master"] = await _repair_master_rows(dry_run)
        elif t == "productions":
            log_job("address_repair", "start", "start", f"target=productions dry_run={dry_run}")
            summary["productions"] = await _repair_production_rows(dry_run)
        elif t == "facilities":
            log_job("address_repair", "start", "start", f"target=facilities dry_run={dry_run}")
            summary["facilities"] = await _repair_facility_rows(dry_run)
        else:
            raise ValueError(f"Unsupported target: {t}")
    return summary


def print_interactive_menu(previews: List[Dict[str, Any]]) -> None:
    print("\nAvailable Databases:")
    for idx, item in enumerate(previews, start=1):
        entry = item["entry"]
        total = item.get("total", 0)
        needs = item.get("needs", 0)
        name = entry.get("name") or entry.get("id")
        print(f"{idx}. {name:<25} ({needs} / {total} need repair)")
    print()


def prompt_for_selection(count: int) -> List[int]:
    raw = input('Select DB(s) to repair (e.g., "1", "2 4", "all", "quit"): ').strip().lower()
    if raw in {"quit", "q", "exit"}:
        return []
    if raw in {"all", "a"}:
        return list(range(1, count + 1))
    parts = [p for p in raw.replace(",", " ").split() if p]
    selected: List[int] = []
    for p in parts:
        if p.isdigit():
            idx = int(p)
            if 1 <= idx <= count:
                selected.append(idx)
    return selected


async def repair_selected_dbs(previews: List[Dict[str, Any]], selection: List[int], dry_run: bool) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for idx in selection:
        item = previews[idx - 1]
        entry = item["entry"]
        rows = item.get("rows") or []
        name = entry.get("name") or entry.get("id") or "Unknown DB"
        if entry["type"] == "master":
            print(f"\nRepairing {name} ({len(rows)} rows)…")
            summary["master"] = await _process_rows(
                rows,
                _build_location_updates,
                update_location_page,
                dry_run,
                category="address_repair",
                collect_diffs=dry_run,
                db_label=entry.get("name") or entry.get("id") or "Locations Master",
            )
            print(f"Finished {name}")
            if dry_run and "diffs" in summary["master"]:
                for rid, diffs in summary["master"]["diffs"].items():
                    _print_full_diffs(rid, diffs)
        elif entry["type"] == "production":
            summary.setdefault("productions", {})
            print(f"\nRepairing {name} ({len(rows)} rows)…")
            result = await _process_rows(
                rows,
                _build_location_updates,
                update_location_page,
                dry_run,
                category="address_repair",
                production_id=entry.get("name") or "",
                log_detail=True,
                collect_diffs=dry_run,
                db_label=entry.get("name") or entry.get("id") or "production",
            )
            summary["productions"][entry.get("name") or entry.get("id")] = result
            print(f"Finished {name}")
            if dry_run and "diffs" in result:
                for rid, diffs in result["diffs"].items():
                    _print_full_diffs(rid, diffs)
        elif entry["type"] == "facility":
            print(f"\nRepairing {name} ({len(rows)} rows)…")
            summary["facilities"] = await _process_rows(
                rows,
                _build_facility_updates,
                update_medical_facility_page,
                dry_run,
                category="address_repair",
                log_detail=True,
                collect_diffs=dry_run,
                db_label=entry.get("name") or entry.get("id") or "Medical Facilities",
            )
            print(f"Finished {name}")
            if dry_run and "diffs" in summary["facilities"]:
                for rid, diffs in summary["facilities"]["diffs"].items():
                    _print_full_diffs(rid, diffs)
    return summary


async def _interactive_main() -> None:
    while True:
        dbs = await discover_all_repairable_dbs()
        if not dbs:
            print("No repairable databases found. Check your configuration.")
            return

        previews = await asyncio.gather(*[preview_db_repairs(entry) for entry in dbs])
        print_interactive_menu(previews)
        selection = prompt_for_selection(len(previews))
        if not selection:
            print("No selection made. Exiting.")
            return

        mode = input("Select mode: 1) Dry run only  2) Apply updates: ").strip()
        dry_run = mode.strip() != "2"

        summary = await repair_selected_dbs(previews, selection, dry_run=dry_run)
        print("\n[address_repair] Summary:")
        for scope, data in summary.items():
            if scope == "productions" and isinstance(data, dict):
                for name, stats in data.items():
                    print(f"  {name}: processed={stats.get('processed', 0)}, updated={stats.get('updated', 0)}, skipped={stats.get('skipped', 0)}, errors={stats.get('errors', 0)}")
            elif isinstance(data, dict):
                print(f"  {scope}: processed={data.get('processed', 0)}, updated={data.get('updated', 0)}, skipped={data.get('skipped', 0)}, errors={data.get('errors', 0)}")
            else:
                print(f"  {scope}: {data}")

        again = input("\nReturn to main menu? (y to continue, any other key to quit): ").strip().lower()
        if again != "y":
            break


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Notion Address Repair Tool (in-place normalization).")
    parser.add_argument("--target", choices=["master", "productions", "facilities", "all"], help="Target dataset(s) to repair.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to Notion.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.target:
        summary = asyncio.run(run_repair(target=args.target, dry_run=args.dry_run))
        print("[address_repair] summary:")
        print(summary)
    else:
        asyncio.run(_interactive_main())


if __name__ == "__main__":
    main()
