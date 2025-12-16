"""Productions fetch and sync endpoints."""

from __future__ import annotations

import asyncio
import logging
import os
import traceback
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, validator
from notion_client import Client

from app.services import background_sync
from app.services.import_jobs import import_locations_for_production
from app.services.job_manager import schedule_job
from app.services.logger import log_job
from app.services.create_production import CreateProductionError, create_production
from config import Config

try:  # pragma: no cover - optional dependency for local dev
    from scripts import notion_utils
    from scripts.notion_utils import format_rich_text, format_status, format_title
except Exception:  # pragma: no cover - defensive import guard
    notion_utils = None  # type: ignore[assignment]
    format_rich_text = None  # type: ignore[assignment]
    format_status = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/productions", tags=["productions"])


async def _production_exists(production_id: str) -> bool:
    prod_lower = (production_id or "").lower()
    try:
        cached = background_sync.get_cached_records()
        for row in cached.get("records", []):
            if str(row.get("ProductionID", "")).lower() == prod_lower:
                return True
    except Exception:
        pass

    try:
        records: List[Dict[str, Any]] = await background_sync.fetch_from_notion()
        return any(str(row.get("ProductionID", "")).lower() == prod_lower for row in records)
    except Exception:
        return False


class CreateProductionRequest(BaseModel):
    production_code: str  # used as abbreviation
    production_name: str
    nickname: str | None = None
    prod_status: str | None = None
    client_platform: str | None = None
    production_type: str | None = None
    studio: str | None = None

    @validator("production_code", "production_name")
    def _not_blank(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("must be a non-empty string")
        return v.strip()


@router.post("/create")
def api_create_production(payload: CreateProductionRequest) -> Dict[str, Any]:
    try:
        result = create_production(
            production_code=payload.production_code,
            production_name=payload.production_name,
            nickname=payload.nickname,
            prod_status=payload.prod_status,
            client_platform=payload.client_platform,
            production_type=payload.production_type,
            studio=payload.studio,
        )
        return {"status": "ok", "result": result}
    except CreateProductionError as exc:
        return {"status": "error", "message": str(exc)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to create production: %s", exc)
        detail = str(exc) if str(exc) else "Unknown error"
        return {"status": "error", "message": f"Failed to create production: {detail}"}


@router.get("/options")
def api_production_options() -> Dict[str, Any]:
    if not Config.NOTION_TOKEN or not Config.PRODUCTIONS_MASTER_DB:
        return {"status": "error", "message": "Missing NOTION_TOKEN or PRODUCTIONS_MASTER_DB"}
    try:
        client = Client(auth=Config.NOTION_TOKEN, notion_version="2022-06-28")
        db = client.databases.retrieve(Config.PRODUCTIONS_MASTER_DB)
        props = db.get("properties") or {}
        prod_status_opts = []
        prod_status_prop = props.get("ProdStatus", {})
        for opt in prod_status_prop.get("status", {}).get("options", []) or []:
            name = opt.get("name")
            if name:
                prod_status_opts.append(name)
        return {
            "status": "ok",
            "prod_status_options": prod_status_opts,
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to fetch production options: %s", exc)
        return {"status": "error", "message": "Failed to fetch production options"}


@router.post("/{production_id}/locations/import")
async def import_locations_for_prod(production_id: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = payload or {}
    addresses_raw = payload.get("addresses")
    duplicate_strategy = str(payload.get("duplicate_strategy") or "skip").lower()

    if not isinstance(addresses_raw, list) or not addresses_raw:
        return {"status": "error", "message": "addresses must be a non-empty list of strings"}

    if duplicate_strategy not in {"skip", "update", "flag"}:
        return {"status": "error", "message": "duplicate_strategy must be one of: skip, update, flag"}

    addresses = [str(addr).strip() for addr in addresses_raw if isinstance(addr, str) and str(addr).strip()]
    if not addresses:
        return {"status": "error", "message": "addresses must be a non-empty list of strings"}

    if not await _production_exists(production_id):
        err = f"Unknown production_id={production_id}"
        log_job("locations_batch_import", "schedule", "error", err)
        return {"status": "error", "message": err}

    try:
        job_id = schedule_job(
            "locations_batch_import",
            lambda: import_locations_for_production(production_id=production_id, addresses=addresses, duplicate_strategy=duplicate_strategy),
        )
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to schedule batch import: {exc}"
        log_job("locations_batch_import", "schedule", "error", err)
        return {"status": "error", "message": err}

    log_job(
        "locations_batch_import",
        "schedule",
        "success",
        f"production_id={production_id} job_id={job_id} addresses={len(addresses)} strategy={duplicate_strategy}",
    )
    return {
        "status": "success",
        "message": "Import job scheduled.",
        "data": {"job_id": job_id},
    }


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
    operation = payload.get("operation")
    if operation == "auto_sync":
        result = await background_sync.trigger_manual_sync()
        status = "success" if result.get("ok") else "error"
        message = result.get("message", "")
        data = background_sync.get_status()
        return {
            "status": status,
            "message": message,
            "data": data,
        }

    if not notion_utils or not format_rich_text or not format_status:
        message = "Notion utilities are unavailable"
        logger.error(message)
        return {"status": "error", "message": message}

    notion_token = os.getenv("NOTION_TOKEN")
    productions_db_id = os.getenv("NOTION_PRODUCTIONS_DB_ID")

    if not notion_token or not productions_db_id:
        message = "Missing NOTION_TOKEN or NOTION_PRODUCTIONS_DB_ID"
        logger.warning(message)
        return {"status": "error", "message": message}

    if operation == "ui_sync":
        updates = payload.get("modified_rows") or []
    else:
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

            # Status fields
            if "ProdStatus" in item and item["ProdStatus"]:
                properties["ProdStatus"] = format_status(item["ProdStatus"])
            if "Status" in item and item["Status"]:
                properties["Status"] = format_status(item["Status"])

            # Date fields
            if "PPFirstDate" in item:
                properties["PPFirstDate"] = {"date": {"start": item.get("PPFirstDate")}}
            if "PPLastDay" in item:
                properties["PPLastDay"] = {"date": {"start": item.get("PPLastDay")}}

            # Text fields (all are rich_text according to schema)
            text_fields = {
                "Name": "Name",
                "Abbreviation": "Abbreviation",
                "Nickname": "Nickname",
                "ClientPlatform": "Client / Platform",
                "Studio": "Studio",
                "ProductionType": "Production Type",
            }
            for ui_key, notion_name in text_fields.items():
                if ui_key in item:
                    value = item[ui_key]
                    properties[notion_name] = format_rich_text(value or "")

            if not properties:
                skipped += 1
                continue

            try:
                notion_utils.update_page(page_id, properties)
                applied += 1
            except Exception as exc:
                logger.error("Failed to sync page %s. Sent properties: %s. Error: %s", page_id, properties, exc, exc_info=True)
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
