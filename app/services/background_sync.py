"""Background sync utilities for Productions data."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.logger import log_job

try:  # pragma: no cover - optional dependency guard
    from scripts import notion_utils
except Exception:  # pragma: no cover
    notion_utils = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

_CACHE_PATH = Path(os.getenv("PRODUCTIONS_CACHE_PATH", "app/data/productions_cache.json"))
_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

_SYNC_ENABLED = os.getenv("PRODUCTIONS_SYNC_ENABLED", "false").lower() == "true"
_cache_lock = asyncio.Lock()
_sync_task: Optional[asyncio.Task] = None
_last_status: Dict[str, Any] = {
    "timestamp": None,
    "count": 0,
    "status": "inactive",
    "message": "Sync not started",
}


def _interval_minutes() -> int:
    try:
        value = int(os.getenv("PRODUCTIONS_SYNC_INTERVAL_MIN", "10"))
        return max(1, value)
    except ValueError:
        return 10


def map_production(page: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a Notion page payload into UI-friendly fields."""

    props = page.get("properties", {})
    title = _extract_title(props)
    status = _extract_status(props)
    start_date_iso, end_date_iso = _extract_date_range(props)
    last_updated_iso = page.get("last_edited_time")

    return {
        "id": page.get("id"),
        "title": title,
        "status": status,
        "start_date": start_date_iso,
        "end_date": end_date_iso,
        "last_updated": last_updated_iso,
    }


def _extract_title(props: Dict[str, Any]) -> str:
    for value in props.values():
        if value.get("type") == "title":
            title_items = value.get("title") or []
            if title_items:
                return title_items[0].get("plain_text") or title_items[0].get("text", {}).get("content", "")
    return "Untitled"


def _extract_status(props: Dict[str, Any]) -> str:
    for value in props.values():
        if value.get("type") == "status":
            option = value.get("status") or {}
            return option.get("name") or ""
    return ""


def _extract_date_range(props: Dict[str, Any]) -> tuple[str | None, str | None]:
    for value in props.values():
        if value.get("type") == "date":
            date_obj = value.get("date") or {}
            return date_obj.get("start"), date_obj.get("end")
    return None, None


async def fetch_from_notion() -> List[Dict[str, Any]]:
    """Return productions directly from Notion."""

    if not notion_utils:
        raise RuntimeError("Notion utilities are unavailable")

    productions_db_id = os.getenv("NOTION_PRODUCTIONS_DB_ID")
    if not productions_db_id:
        raise RuntimeError("Missing NOTION_PRODUCTIONS_DB_ID")

    def worker() -> List[Dict[str, Any]]:
        pages = notion_utils.query_database(productions_db_id)  # type: ignore[union-attr]
        return [map_production(page) for page in pages]

    return await asyncio.to_thread(worker)


async def trigger_manual_sync() -> Dict[str, Any]:
    """Run a one-off sync (used by Settings UI)."""

    return await _sync_once(action="manual_sync")


def get_cached_records() -> Dict[str, Any]:
    """Return cached records plus timestamp."""

    if not _CACHE_PATH.exists():
        return {"records": [], "timestamp": None}

    try:
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"records": [], "timestamp": None}
    return {
        "records": data.get("records", []),
        "timestamp": data.get("timestamp"),
    }


def get_status() -> Dict[str, Any]:
    """Expose last sync metadata for the API."""

    cache = get_cached_records()
    cache_timestamp = cache.get("timestamp")
    cache_count = len(cache.get("records", []))
    return {
        "auto_sync_enabled": _SYNC_ENABLED,
        "interval_minutes": _interval_minutes(),
        "cache_path": str(_CACHE_PATH),
        "last_sync_timestamp": _last_status.get("timestamp") or cache_timestamp,
        "last_status": _last_status.get("status"),
        "last_message": _last_status.get("message"),
        "record_count": _last_status.get("count") or cache_count,
        "cache_timestamp": cache_timestamp,
        "cache_record_count": cache_count,
    }


def ensure_started() -> None:
    """Kick off the background loop when auto-sync is enabled."""

    global _sync_task

    if not _SYNC_ENABLED:
        logger.info("Productions background sync disabled via PRODUCTIONS_SYNC_ENABLED")
        return
    if not notion_utils:
        logger.warning("Cannot start productions background sync: notion_utils unavailable")
        return
    if _sync_task and not _sync_task.done():
        return

    loop = asyncio.get_running_loop()
    logger.info("Starting productions background sync loop (interval=%s min)", _interval_minutes())
    _sync_task = loop.create_task(_sync_loop())


async def _sync_loop() -> None:
    """Continuously refresh the productions cache."""

    while True:
        await _sync_once(action="auto_sync")
        await asyncio.sleep(_interval_minutes() * 60)


async def _sync_once(action: str) -> Dict[str, Any]:
    """Run a single sync cycle (auto or manual)."""

    try:
        records = await fetch_from_notion()
    except Exception as exc:  # noqa: BLE001
        message = f"Productions sync failed: {exc}"
        logger.error(message)
        _update_last_status(status="error", message=message, count=0, timestamp=None)
        log_job("Productions Sync", action, "error", message)
        return {"ok": False, "message": message}

    timestamp = _utc_now()
    await _write_cache(records, timestamp)

    message = f"Cached {len(records)} productions at {timestamp}"
    _update_last_status(status="success", message=message, count=len(records), timestamp=timestamp)
    log_job("Productions Sync", action, "success", message)
    return {"ok": True, "message": message, "timestamp": timestamp, "count": len(records)}


async def _write_cache(records: List[Dict[str, Any]], timestamp: str) -> None:
    payload = {"records": records, "timestamp": timestamp}
    async with _cache_lock:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _update_last_status(status: str, message: str, count: int, timestamp: Optional[str]) -> None:
    _last_status.update(
        {
            "status": status,
            "message": message,
            "count": count,
            "timestamp": timestamp,
        }
    )


def _utc_now() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
