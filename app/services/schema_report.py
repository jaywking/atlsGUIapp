from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import httpx

from app.services import background_sync
from app.services.notion_locations import get_locations_db_id_from_url
from config import Config


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "docs" / "schema_reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def _collect_db_ids_from_config() -> Dict[str, str]:
    """Collect database IDs from Config attributes (env-driven)."""
    Config.setup()
    db_sources: Dict[str, str] = {}
    for attr in dir(Config):
        if (attr.endswith("_DB") or attr.endswith("_DB_ID")) and not attr.startswith("_"):
            db_id = getattr(Config, attr, "")
            if isinstance(db_id, str) and len(db_id.replace("-", "")) == 32:
                db_sources[db_id] = f".env::{attr}"
    return db_sources


def _collect_db_ids_from_env() -> Dict[str, str]:
    """Collect database IDs directly from environment variables."""
    db_sources: Dict[str, str] = {}
    for key, value in os.environ.items():
        if not (key.endswith("_DB") or key.endswith("_DB_ID")):
            continue
        if isinstance(value, str) and len(value.replace("-", "")) == 32:
            db_sources[value] = f"env::{key}"
    return db_sources


def _collect_db_ids_from_json(filepath: Path) -> Dict[str, str]:
    """Collect database IDs from notion_tables.json (if present)."""
    db_sources: Dict[str, str] = {}
    try:
        with filepath.open("r", encoding="utf-8") as f:
            prod_dbs = json.load(f)
        for name, db_id in prod_dbs.items():
            if isinstance(db_id, str) and len(db_id.replace("-", "")) == 32:
                db_sources.setdefault(db_id, f"{filepath.name}::{name}")
    except Exception:
        # best-effort; skip silently
        return db_sources
    return db_sources


async def _fetch_database(db_id: str) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {Config.NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"https://api.notion.com/v1/databases/{db_id}", headers=headers)
        resp.raise_for_status()
        return resp.json()


def _format_property_lines(name: str, meta: Dict[str, Any]) -> List[str]:
    prop_type = meta.get("type", "")
    line = f"  - {name} (Type: {prop_type})"
    lines = [line]
    options = []
    if prop_type in {"select", "multi_select", "status"}:
        options = meta.get(prop_type, {}).get("options", [])
    if options:
        option_names = [f"'{opt.get('name', '')}'" for opt in options if isinstance(opt, dict)]
        lines[-1] = f"{line} (Options: {', '.join(option_names)})"
    return lines


async def _collect_psl_db_ids() -> Tuple[Dict[str, str], List[str], List[str]]:
    """Gather PSL database IDs from Productions Master records."""
    sources: Dict[str, str] = {}
    missing: List[str] = []
    invalid: List[str] = []
    try:
        productions = await background_sync.fetch_from_notion()
    except Exception as exc:  # noqa: BLE001
        return {}, [f"Failed to load productions: {exc}"], invalid

    for prod in productions:
        name = prod.get("Name") or prod.get("ProductionID") or "Unknown Production"
        loc_url = prod.get("LocationsTable") or ""
        if not loc_url:
            missing.append(f"{name}")
            continue
        db_id = get_locations_db_id_from_url(loc_url)
        if not db_id:
            invalid.append(f"{name} (bad link: {loc_url})")
            continue
        if len(db_id.replace("-", "")) != 32:
            invalid.append(f"{name} (bad id: {db_id})")
            continue
        sources.setdefault(db_id, f"PSL::{name}")
    return sources, missing, invalid


async def generate_schema_report_stream() -> Iterable[str]:
    """Yield progress lines while generating a plain-text schema report."""
    db_sources: Dict[str, str] = {}
    db_sources.update(_collect_db_ids_from_config())
    db_sources.update(_collect_db_ids_from_env())
    db_sources.update(_collect_db_ids_from_json(PROJECT_ROOT / "notion_tables.json"))

    psl_sources, missing_psl, invalid_psl = await _collect_psl_db_ids()

    if not db_sources and not psl_sources:
        yield "No database IDs found; add *_DB or *_DB_ID env vars or notion_tables.json entries.\n"
        return

    yield f"Discovered {len(db_sources)} canonical database ids.\n"
    yield f"Discovered {len(psl_sources)} PSL database ids.\n"

    timestamp = time.strftime("%Y-%m-%d_%H%M%S")
    output_path = REPORT_DIR / f"schema_report_{timestamp}.txt"
    report_lines: List[str] = [
        "Notion Database Schema Report",
        f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "Summary:",
        f"- Total databases: {len(db_sources) + len(psl_sources)}",
        f"- Canonical databases: {len(db_sources)}",
        f"- PSL databases: {len(psl_sources)}",
        f"- Productions missing PSL DB link: {len(missing_psl)}",
        f"- Productions with invalid PSL DB link: {len(invalid_psl)}",
        "- Fatal fetch failures: noted inline per database",
        "=" * 50,
        "",
    ]

    if missing_psl:
        report_lines.append("Warnings - productions missing PSL DB link:")
        report_lines.extend([f"- {m}" for m in missing_psl])
        report_lines.append("")
    if invalid_psl:
        report_lines.append("Warnings - productions with invalid PSL DB link:")
        report_lines.extend([f"- {m}" for m in invalid_psl])
        report_lines.append("")

    # Maintain order: canonical first, then PSL (dedup by db_id)
    combined: List[Tuple[str, str, str]] = []  # (db_id, source, kind)
    seen: set[str] = set()
    for db_id, source in sorted(db_sources.items()):
        seen.add(db_id)
        combined.append((db_id, source, "canonical"))
    for db_id, source in sorted(psl_sources.items()):
        if db_id in seen:
            continue
        combined.append((db_id, source, "psl"))

    total = len(combined)
    for idx, (db_id, source, kind) in enumerate(combined, start=1):
        yield f"Row {idx}/{total}\n"
        yield f"Inspecting {db_id} ({source})...\n"
        try:
            data = await _fetch_database(db_id)
            db_title = data.get("title", [{}])[0].get("plain_text", "Untitled")
            report_lines.extend(
                [
                    f"Database: '{db_title}'",
                    f"ID: {db_id}",
                    f"Source: {source if kind == 'canonical' else f'PSL ({source})'}",
                    "-" * 30,
                ]
            )
            properties = sorted((data.get("properties") or {}).items())
            for name, meta in properties:
                report_lines.extend(_format_property_lines(name, meta if isinstance(meta, dict) else {}))
            report_lines.extend(["", "=" * 50, ""])
        except Exception as exc:  # noqa: BLE001
            report_lines.extend(
                [
                    "Database: UNKNOWN",
                    f"ID: {db_id}",
                    f"Source: {source}",
                    f"  - FAILED TO FETCH SCHEMA: {exc}",
                    "",
                    "=" * 50,
                    "",
                ]
            )
            yield f"Failed to fetch schema for {db_id}: {exc}\n"

    output_path.write_text("\n".join(report_lines), encoding="utf-8")
    yield f"Report written to: {output_path}\n"
