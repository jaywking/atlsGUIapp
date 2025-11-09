"""Utilities for pruning and archiving job logs."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = DATA_DIR / "jobs.log"
ARCHIVE_DIR = DATA_DIR / "archive"

DEFAULT_MAX_DAYS = 7
DEFAULT_MAX_ENTRIES = 1000


def _ensure_paths() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.touch()


def _get_setting(name: str, fallback: int) -> int:
    try:
        return int(os.getenv(name, fallback))
    except (TypeError, ValueError):
        return fallback


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    trimmed = value.rstrip("Z")
    try:
        return datetime.fromisoformat(trimmed)
    except ValueError:
        return None


def prune_logs(
    max_days: Optional[int] = None,
    max_entries: Optional[int] = None,
) -> Dict[str, int]:
    """Prune log entries by age and count. Returns summary stats."""

    _ensure_paths()

    if max_days is None:
        max_days = _get_setting("LOG_ROTATE_DAYS", DEFAULT_MAX_DAYS)
    if max_entries is None:
        max_entries = _get_setting("LOG_MAX_ENTRIES", DEFAULT_MAX_ENTRIES)

    with LOG_FILE.open("r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f if line.strip()]

    if not raw_lines:
        return {"kept": 0, "archived": 0}

    entries: List[Dict[str, Any]] = []
    for line in raw_lines:
        try:
            entry = json.loads(line)
        except Exception:
            continue
        entry["_ts"] = _parse_timestamp(entry.get("timestamp"))
        entries.append(entry)

    cutoff = None
    if max_days and max_days > 0:
        cutoff = datetime.utcnow() - timedelta(days=max_days)

    kept: List[Dict[str, Any]] = []
    archived: List[Dict[str, Any]] = []

    for entry in entries:
        ts = entry.get("_ts")
        if cutoff and (ts is None or ts < cutoff):
            archived.append(entry)
        else:
            kept.append(entry)

    if max_entries and max_entries > 0 and len(kept) > max_entries:
        overflow = len(kept) - max_entries
        archived.extend(kept[:overflow])
        kept = kept[overflow:]

    _write_log(kept)
    archive_old_logs(archived)

    return {"kept": len(kept), "archived": len(archived)}


def archive_old_logs(entries: List[Dict[str, Any]]) -> Optional[Path]:
    """Append archived entries to a date-stamped JSONL file."""

    if not entries:
        return None

    _ensure_paths()
    archive_file = ARCHIVE_DIR / f"{datetime.utcnow():%Y%m%d}_jobs.jsonl"
    with archive_file.open("a", encoding="utf-8") as f:
        for entry in entries:
            entry.pop("_ts", None)
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return archive_file


def _write_log(entries: List[Dict[str, Any]]) -> None:
    with LOG_FILE.open("w", encoding="utf-8") as f:
        for entry in entries:
            entry.pop("_ts", None)
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
