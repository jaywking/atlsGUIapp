"""Productions fetch and sync endpoints."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict

from fastapi import APIRouter

from app.services import background_sync
from app.services.logger import log_job

try:  # pragma: no cover - optional dependency for local dev
    from scripts import notion_utils
except Exception:  # pragma: no cover - defensive import guard
    notion_utils = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/productions", tags=["productions"])


@router.get("/fetch")
async def fetch_productions() -> Dict[str, Any]:
    """Fetch production records from Notion (with cache fallback)."""

    cache_used = False

    try:
        records = await background_sync.fetch_from_notion()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Productions fetch failed; attempting cache fallback: %s", exc)
        cache = background_sync.get_cached_records()
        records = cache.get("records", [])
        if records:
            cache_used = True
            message = f"Served {len(records)} cached productions (Notion unavailable)"
        else:
            err = f"Failed to fetch productions: {exc}"
            log_job("Productions Sync", "fetch", "error", err)
            return {"status": "error", "message": err, "data": []}
    else:
        message = f"Fetched {len(records)} productions"

    log_job("Productions Sync", "fetch", "success", message)
    response = {"status": "success", "message": message, "data": records}
    if cache_used:
        response["source"] = "cache"
    return response


@router.post("/sync")
async def sync_productions(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Handle manual auto-sync or push updates to Notion."""

    payload = payload or {}
    if payload.get("operation") == "auto_sync":
        result = await background_sync.trigger_manual_sync()
        status = "success" if result.get("ok") else "error"
        message = result.get("message", "")
        data = background_sync.get_status()
        return {
            "status": status,
            "message": message,
            "data": data,
        }

    if not notion_utils:
        message = "Notion utilities are unavailable"
        logger.error(message)
        return {"status": "error", "message": message}

    notion_token = os.getenv("NOTION_TOKEN")
    productions_db_id = os.getenv("NOTION_PRODUCTIONS_DB_ID")

    if not notion_token or not productions_db_id:
        message = "Missing NOTION_TOKEN or NOTION_PRODUCTIONS_DB_ID"
        logger.warning(message)
        return {"status": "error", "message": message}

    updates = payload.get("updates") or []
    if not isinstance(updates, list):
        updates = []

    def _worker() -> Dict[str, int]:
        applied = 0
        skipped = 0
        for item in updates:
            page_id = item.get("id")
            if not page_id:
                skipped += 1
                continue

            properties: Dict[str, Any] = {}
            status_val = item.get("status")
            if status_val:
                properties["Status"] = {"status": {"name": status_val}}

            start_date = item.get("start_date")
            if start_date:
                properties["Start Date"] = {"date": {"start": start_date}}

            if not properties:
                skipped += 1
                continue

            try:
                notion_utils.update_page(page_id, properties)  # type: ignore[union-attr]
                applied += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("Unable to sync production %s: %s", page_id, exc)
                skipped += 1
        return {"applied": applied, "skipped": skipped}

    try:
        stats = await asyncio.to_thread(_worker)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to sync productions: {exc}"
        logger.exception(err)
        log_job("Productions Sync", "sync", "error", err)
        return {"status": "error", "message": err}

    message = f"Synced {stats['applied']} productions (skipped {stats['skipped']})"
    log_job("Productions Sync", "sync", "success", message)
    return {"status": "success", "message": message, "stats": stats}


@router.get("/status")
async def productions_status() -> Dict[str, Any]:
    """Return metadata about the background sync/cache."""

    data = background_sync.get_status()
    return {"status": "success", "message": "Productions sync status", "data": data}
