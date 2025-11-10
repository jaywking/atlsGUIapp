"""Productions fetch and sync endpoints."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter

from app.services.logger import log_job

try:  # pragma: no cover - optional dependency for local dev
    from scripts import notion_utils
except Exception:  # pragma: no cover - defensive import guard
    notion_utils = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/productions", tags=["productions"])


@router.get("/fetch")
async def fetch_productions() -> Dict[str, Any]:
    """Fetch production records from Notion."""

    if not notion_utils:
        message = "Notion utilities are unavailable"
        logger.error(message)
        return {"status": "error", "message": message, "data": []}

    notion_token = os.getenv("NOTION_TOKEN")
    productions_db_id = os.getenv("NOTION_PRODUCTIONS_DB_ID")

    if not notion_token or not productions_db_id:
        message = "Missing NOTION_TOKEN or NOTION_PRODUCTIONS_DB_ID"
        logger.warning(message)
        return {"status": "error", "message": message, "data": []}

    def _worker() -> List[Dict[str, Any]]:
        pages = notion_utils.query_database(productions_db_id)  # type: ignore[union-attr]
        return [_map_production(page) for page in pages]

    try:
        records = await asyncio.to_thread(_worker)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to fetch productions: {exc}"
        logger.exception(err)
        log_job("Productions Sync", "fetch", "error", err)
        return {"status": "error", "message": err, "data": []}

    message = f"Fetched {len(records)} productions"
    log_job("Productions Sync", "fetch", "success", message)
    return {"status": "success", "message": message, "data": records}


@router.post("/sync")
async def sync_productions(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Push updates to Notion by syncing status / start dates."""

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

    updates = (payload or {}).get("updates") or []
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


def _map_production(page: Dict[str, Any]) -> Dict[str, Any]:
    props = page.get("properties", {})
    title = _extract_title(props)
    status = _extract_status(props)
    start_date_iso = _extract_start_date(props)
    last_updated_iso = page.get("last_edited_time")

    return {
        "id": page.get("id"),
        "title": title,
        "status": status,
        "start_date": start_date_iso,
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


def _extract_start_date(props: Dict[str, Any]) -> str | None:
    for value in props.values():
        if value.get("type") == "date":
            date_obj = value.get("date") or {}
            return date_obj.get("start")
    return None
