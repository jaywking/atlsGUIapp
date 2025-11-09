"""Dashboard summary endpoint."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from app.services.logger import read_logs
from app.services.config_tester import check_maps_connection, check_notion_connection

try:  # Import lazily so the app still loads without legacy scripts.
    from scripts import notion_utils
except Exception:  # pragma: no cover - defensive import guard
    notion_utils = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary() -> Dict[str, Any]:
    """Return aggregate counts, recent jobs, and service connectivity."""

    notion_token = os.getenv("NOTION_TOKEN")
    productions_db_id = os.getenv("NOTION_PRODUCTIONS_DB_ID")
    locations_db_id = os.getenv("NOTION_LOCATIONS_DB_ID")
    maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    notion_task = asyncio.create_task(
        _fetch_notion_counts(notion_token, productions_db_id, locations_db_id)
    )
    status_task = asyncio.create_task(
        _check_service_statuses(notion_token, locations_db_id, maps_api_key)
    )

    recent_jobs = _collect_recent_jobs()

    notion_counts, statuses = await asyncio.gather(notion_task, status_task)

    summary = {
        "productions_total": notion_counts.get("productions", 0),
        "locations_total": notion_counts.get("locations", 0),
        "recent_jobs": recent_jobs,
        "notion_status": statuses.get("notion", "unknown"),
        "maps_status": statuses.get("maps", "unknown"),
    }

    return summary


def _collect_recent_jobs(limit_hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
    """Return jobs within the last ``limit_hours`` sorted newest-first."""

    entries = read_logs()
    if not entries:
        return []

    cutoff = datetime.utcnow() - timedelta(hours=limit_hours)
    recent: List[Dict[str, Any]] = []
    for entry in entries:
        ts = _parse_timestamp(entry.get("timestamp"))
        if ts is None or ts < cutoff:
            continue
        recent.append({
            "timestamp": entry.get("timestamp"),
            "category": entry.get("category"),
            "status": entry.get("status"),
            "message": entry.get("message"),
        })

    recent.sort(
        key=lambda item: _parse_timestamp(item.get("timestamp")) or datetime.min,
        reverse=True,
    )
    return recent[:limit]


def _parse_timestamp(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    raw = raw.rstrip("Z")
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


async def _fetch_notion_counts(
    token: Optional[str], productions_db_id: Optional[str], locations_db_id: Optional[str]
) -> Dict[str, int]:
    """Fetch totals from Notion databases when credentials are available."""

    if not token or not notion_utils:
        return {"productions": 0, "locations": 0}

    async def _count(db_id: Optional[str]) -> int:
        if not db_id:
            return 0

        def worker() -> int:
            try:
                results = notion_utils.query_database(db_id)
                return len(results)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Notion count failed for %s: %s", db_id, exc)
                return 0

        return await asyncio.to_thread(worker)

    productions_count, locations_count = await asyncio.gather(
        _count(productions_db_id),
        _count(locations_db_id),
    )

    return {"productions": productions_count, "locations": locations_count}


async def _check_service_statuses(
    notion_token: Optional[str], notion_db_id: Optional[str], maps_key: Optional[str]
) -> Dict[str, str]:
    """Return connectivity labels for Notion and Google Maps."""

    notion_ok = False
    notion_label = "missing-token"
    if notion_token:
        notion_ok, notion_message = await check_notion_connection(notion_token, notion_db_id)
        notion_label = "connected" if notion_ok else notion_message or "error"

    maps_ok = False
    maps_label = "missing-key"
    if maps_key:
        maps_ok, maps_message = await check_maps_connection(maps_key)
        maps_label = "connected" if maps_ok else maps_message or "error"

    if not notion_token:
        notion_label = "missing-token"
    if not maps_key:
        maps_label = "missing-key"

    return {
        "notion": notion_label.lower(),
        "maps": maps_label.lower(),
    }

