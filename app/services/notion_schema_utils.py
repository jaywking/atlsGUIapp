from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

import httpx

from app.services.logger import log_job
from config import Config

NOTION_VERSION = "2022-06-28"
SEARCH_URL = "https://api.notion.com/v1/search"
DATABASE_URL = "https://api.notion.com/v1/databases"


def _headers() -> Dict[str, str]:
    token = Config.NOTION_TOKEN
    if not token:
        raise RuntimeError("Missing NOTION_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


async def search_location_databases() -> List[Dict[str, Any]]:
    headers = _headers()
    payload = {
        "query": "_Locations",
        "filter": {"value": "database", "property": "object"},
        "page_size": 100,
        "sort": {"direction": "descending", "timestamp": "last_edited_time"},
    }

    items: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        start_cursor: str | None = None
        while True:
            body = dict(payload)
            if start_cursor:
                body["start_cursor"] = start_cursor
            resp = await client.post(SEARCH_URL, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            items.extend(results)
            if not data.get("has_more"):
                break
            start_cursor = data.get("next_cursor")
    # Filter titles ending with _Locations
    filtered: List[Dict[str, Any]] = []
    for item in items:
        if item.get("object") != "database":
            continue
        title_blocks = item.get("title") or []
        title_text = "".join([t.get("plain_text", "") for t in title_blocks if isinstance(t, dict)])
        if title_text.endswith("_Locations"):
            filtered.append(item)
    return filtered


async def fetch_database(db_id: str) -> Dict[str, Any]:
    headers = _headers()
    url = f"{DATABASE_URL}/{db_id}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def patch_database(db_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    headers = _headers()
    url = f"{DATABASE_URL}/{db_id}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.patch(url, headers=headers, json={"properties": properties})
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:  # noqa: BLE001
            body = ""
            try:
                body = resp.text
            except Exception:
                body = ""
            raise httpx.HTTPStatusError(f"{exc} body={body}", request=exc.request, response=resp)
        return resp.json()


def _missing_props(existing_props: Dict[str, Any], required: Dict[str, Any]) -> Dict[str, Any]:
    to_add: Dict[str, Any] = {}
    for key, schema in required.items():
        if key not in existing_props:
            to_add[key] = schema
    return to_add


def _status_has_unresolved(status_prop: Dict[str, Any]) -> Tuple[bool, str]:
    if not status_prop or status_prop.get("type") != "status":
        return False, "missing_or_non_status"
    options = status_prop.get("status", {}).get("options", [])
    names = {opt.get("name") for opt in options if isinstance(opt, dict)}
    return "Unresolved" in names, "already_present" if "Unresolved" in names else "missing_option"


async def ensure_schema(db_id: str) -> Tuple[bool, List[str]]:
    """Ensure the target database has required canonical address fields and Status includes Unresolved.

    Returns (updated, updated_fields).
    """
    db = await fetch_database(db_id)
    props = db.get("properties") or {}
    required_props = {
        "address1": {"rich_text": {}},
        "address2": {"rich_text": {}},
        "address3": {"rich_text": {}},
        "city": {"rich_text": {}},
        "state": {"rich_text": {}},
        "zip": {"rich_text": {}},
        "country": {"rich_text": {}},
        "county": {"rich_text": {}},
        "borough": {"rich_text": {}},
        "formatted_address_google": {"rich_text": {}},
        "Full Address": {"rich_text": {}},
        "Place_ID": {"rich_text": {}},
        "Latitude": {"number": {}},
        "Longitude": {"number": {}},
    }

    missing = _missing_props(props, required_props)
    updated_fields: List[str] = list(missing.keys())
    body: Dict[str, Any] = {}
    if missing:
        body["properties"] = missing

    status_prop = props.get("Status") or {}
    has_unresolved, status_reason = _status_has_unresolved(status_prop)
    if status_reason == "missing_or_non_status":
        log_job("schema_update", "skip", "error", f"db_id={db_id} status_property_missing_or_wrong_type")
    elif not has_unresolved:
        # Notion does not allow updating Status options via API; log and continue.
        log_job("schema_update", "skip", "error", f"db_id={db_id} status_unresolved_missing_manual_update_required")

    if not body:
        return False, []

    await patch_database(db_id, body["properties"])
    log_job("schema_update", "patch", "success", f"db_id={db_id} fields={updated_fields}")
    return True, updated_fields


async def ensure_all_schemas() -> Tuple[List[str], List[str], List[str]]:
    """Ensure schemas for all _Locations DBs, Locations Master, and Medical Facilities.

    Returns (updated, skipped, failed)
    """
    updated: List[str] = []
    skipped: List[str] = []
    failed: List[str] = []

    db_ids: Set[str] = set()
    try:
        search_results = await search_location_databases()
        for item in search_results:
            db_id = item.get("id")
            if db_id:
                db_ids.add(db_id)
    except Exception as exc:  # noqa: BLE001
        log_job("schema_update", "search", "error", f"search_failed: {exc}")

    if Config.LOCATIONS_MASTER_DB:
        db_ids.add(Config.LOCATIONS_MASTER_DB)
    if Config.MEDICAL_FACILITIES_DB:
        db_ids.add(Config.MEDICAL_FACILITIES_DB)

    for db_id in db_ids:
        try:
            changed, fields = await ensure_schema(db_id)
            if changed:
                updated.append(db_id)
            else:
                skipped.append(db_id)
                log_job("schema_update", "skip", "success", f"db_id={db_id} no_changes")
        except Exception as exc:  # noqa: BLE001
            failed.append(db_id)
            log_job("schema_update", "patch", "error", f"db_id={db_id} error={exc}")

    return updated, skipped, failed
