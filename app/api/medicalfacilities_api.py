from __future__ import annotations

import asyncio
import math
import sys
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter

from app.services.logger import log_job
from config import Config
from scripts import fetch_medical_facilities as run_fetch_medical_facilities

NOTION_VERSION = "2022-06-28"

router = APIRouter(prefix="/api/medicalfacilities", tags=["medical facilities"])


def _rich_text(props: Dict[str, Any], key: str) -> str:
    arr = props.get(key, {}).get("rich_text", [])
    return " ".join([a.get("plain_text", "") for a in arr if isinstance(a, dict)]) if arr else ""


def _title(props: Dict[str, Any], key: str) -> str:
    arr = props.get(key, {}).get("title", [])
    return " ".join([a.get("plain_text", "") for a in arr if isinstance(a, dict)]) if arr else ""


def _url(props: Dict[str, Any], key: str) -> str:
    return props.get(key, {}).get("url") or ""


def _select(props: Dict[str, Any], key: str) -> str:
    sel = props.get(key, {}).get("select") or {}
    return sel.get("name") or ""


def _multi(props: Dict[str, Any], key: str) -> List[str]:
    return [m.get("name", "") for m in props.get(key, {}).get("multi_select", []) if m.get("name")]


def _number(props: Dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        num = props.get(key, {}).get("number")
        if num is not None:
            return float(num)
    return None


def _build_hours(props: Dict[str, Any]) -> str:
    days = [
        ("Monday Hours", "Mon"),
        ("Tuesday Hours", "Tue"),
        ("Wednesday Hours", "Wed"),
        ("Thursday Hours", "Thu"),
        ("Friday Hours", "Fri"),
        ("Saturday Hours", "Sat"),
        ("Sunday Hours", "Sun"),
    ]
    parts = []
    for prop_name, label in days:
        val = _rich_text(props, prop_name)
        if val:
            parts.append(f"{label}: {val}")
    return "; ".join(parts)


def _normalize_facility(page: Dict[str, Any]) -> Dict[str, Any]:
    props = page.get("properties") or {}
    facility_id = _title(props, "MedicalFacilityID") or _rich_text(props, "MedicalFacilityID")
    name = _rich_text(props, "Name") or facility_id
    facility_type = _select(props, "Type")
    distance_val = _number(props, "Distance", "Distance (mi)")
    phone_val = _rich_text(props, "Phone") or _rich_text(props, "International Phone")

    return {
        "row_id": page.get("id") or "",
        "id": page.get("id") or "",
        "medical_facility_id": facility_id or "",
        "name": name or facility_id or "Unnamed Facility",
        "facility_type": facility_type,
        "address": _rich_text(props, "Address"),
        "phone": phone_val,
        "hours": _build_hours(props),
        "website": _url(props, "Website"),
        "google_maps_url": _url(props, "Google Maps URL"),
        "distance": distance_val,
        "place_types": [facility_type] if facility_type else [],
        "place_id": _rich_text(props, "Place_ID"),
    }


async def _fetch_facilities(db_id: str, token: str) -> List[Dict[str, Any]]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    items: List[Dict[str, Any]] = []
    start_cursor: str | None = None

    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            payload: Dict[str, Any] = {"page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            items.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            start_cursor = data.get("next_cursor")
    return items


@router.get("/list")
async def list_medical_facilities(page: int = 1, limit: int = 25) -> Dict[str, Any]:
    page = max(1, page)
    limit = min(100, max(1, limit))

    db_id = Config.MEDICAL_FACILITIES_DB
    token = Config.NOTION_TOKEN
    if not token or not db_id:
        return {"status": "error", "message": "Missing NOTION_TOKEN or MEDICAL_FACILITIES_DB"}

    try:
        pages = await _fetch_facilities(db_id, token)
    except Exception as exc:  # noqa: BLE001
        err = f"Unable to load medical facilities: {exc}"
        log_job("facilities", "list", "error", err)
        return {"status": "error", "message": err}

    total = len(pages)
    total_pages = max(1, math.ceil(total / limit)) if total else 1
    start = (page - 1) * limit
    end = start + limit
    sliced = pages[start:end]
    items = [_normalize_facility(p) for p in sliced]

    message = f"Returned page {page} of {total_pages} ({total} total)"
    log_job("facilities", "list", "success", message)
    return {
        "status": "success",
        "message": message,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
        },
    }


def _run_facility_job() -> dict:
    original_argv = sys.argv[:]  # avoid argparse consuming uvicorn arguments
    sys.argv = ["fetch_medical_facilities"]
    try:
        result = run_fetch_medical_facilities()
        message = str(result)
        log_job(category="facilities", action="fill", status="success", message=message)
        return {"status": "success", "message": message}
    except BaseException as exc:  # noqa: BLE001
        err = f"{exc}"
        log_job(category="facilities", action="fill", status="error", message=err)
        return {"status": "error", "message": err}
    finally:
        sys.argv = original_argv


@router.post("/fill")
async def fill_facilities() -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _run_facility_job)
    return result
