from __future__ import annotations

import argparse
from typing import Dict, List
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
script_dir = Path(__file__).resolve().parent
sys.path = [p for p in sys.path if Path(p).resolve() != script_dir]
sys.path.insert(0, str(project_root))
from config import Config  # noqa: E402
from scripts import notion_utils as nu  # noqa: E402

DAYS = [
    ("Monday Hours", "Monday"),
    ("Tuesday Hours", "Tuesday"),
    ("Wednesday Hours", "Wednesday"),
    ("Thursday Hours", "Thursday"),
    ("Friday Hours", "Friday"),
    ("Saturday Hours", "Saturday"),
    ("Sunday Hours", "Sunday"),
]


def _rich_text_value(props: Dict[str, Dict], key: str) -> str:
    arr = props.get(key, {}).get("rich_text", [])
    return " ".join([a.get("plain_text", "") for a in arr if isinstance(a, dict)]).strip()


def _strip_day_prefix(value: str, day_name: str) -> str:
    text = value.strip()
    prefix = f"{day_name}:"
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix) :].strip()
    return text


def _build_updates(props: Dict[str, Dict]) -> Dict[str, Dict]:
    updates: Dict[str, Dict] = {}
    for prop_name, day_name in DAYS:
        current = _rich_text_value(props, prop_name)
        if not current:
            continue
        cleaned = _strip_day_prefix(current, day_name)
        if cleaned != current:
            updates[prop_name] = nu.format_rich_text(cleaned)
    return updates


def clean_hours(dry_run: bool) -> None:
    db_id = Config.MEDICAL_FACILITIES_DB
    if not db_id:
        raise RuntimeError("Missing MEDICAL_FACILITIES_DB")

    pages = nu.query_database(db_id)
    total = len(pages)
    updated = 0
    skipped = 0

    for page in pages:
        page_id = page.get("id") or ""
        props = page.get("properties") or {}
        updates = _build_updates(props)
        if not updates:
            skipped += 1
            continue

        updated += 1
        if dry_run:
            print(f"[DRY-RUN] page_id={page_id} updates={list(updates.keys())}")
            continue

        nu.update_page(page_id, updates)
        print(f"updated page_id={page_id} fields={list(updates.keys())}")

    print(f"Done. total={total} updated={updated} skipped={skipped} dry_run={dry_run}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Strip weekday prefixes from Medical Facilities hours fields.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing to Notion.")
    args = parser.parse_args()
    clean_hours(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
