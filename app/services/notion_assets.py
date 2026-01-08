from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx

from config import Config

NOTION_VERSION = "2022-06-28"
PAGE_SIZE = 100


def _headers() -> Dict[str, str]:
    token = Config.NOTION_TOKEN
    if not token:
        raise RuntimeError("Missing NOTION_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _require_prop(props: Dict[str, Any], key: str) -> Dict[str, Any]:
    if key not in props:
        raise ValueError(f"Missing Assets property: {key}")
    return props[key] or {}


def _title(props: Dict[str, Any], key: str) -> str:
    prop = _require_prop(props, key)
    items = prop.get("title") or []
    return " ".join([i.get("plain_text", "") for i in items if isinstance(i, dict)]).strip()


def _rich_text(props: Dict[str, Any], key: str) -> str:
    prop = _require_prop(props, key)
    items = prop.get("rich_text") or []
    return " ".join([i.get("plain_text", "") for i in items if isinstance(i, dict)]).strip()


def _select(props: Dict[str, Any], key: str) -> str:
    prop = _require_prop(props, key)
    selected = prop.get("select") or {}
    return (selected.get("name") or "").strip()


def _multi_select(props: Dict[str, Any], key: str) -> List[str]:
    prop = _require_prop(props, key)
    items = prop.get("multi_select") or []
    return [i.get("name") for i in items if isinstance(i, dict) and i.get("name")]


def _url(props: Dict[str, Any], key: str) -> str:
    prop = _require_prop(props, key)
    return (prop.get("url") or "").strip()


def _relation_ids(props: Dict[str, Any], key: str) -> List[str]:
    prop = _require_prop(props, key)
    rels = prop.get("relation") or []
    return [rel.get("id") for rel in rels if rel.get("id")]


def _date(props: Dict[str, Any], key: str) -> str:
    prop = _require_prop(props, key)
    date = prop.get("date") or {}
    return (date.get("start") or "").strip()


def _extract_title_generic(props: Dict[str, Any]) -> str:
    for value in props.values():
        if isinstance(value, dict) and value.get("type") == "title":
            items = value.get("title") or []
            if items:
                return items[0].get("plain_text") or items[0].get("text", {}).get("content", "") or ""
    return ""


async def _query_assets(filter_block: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    db_id = Config.ASSETS_DB_ID
    if not db_id:
        raise RuntimeError("Missing ASSETS_DB_ID")

    headers = _headers()
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    items: List[Dict[str, Any]] = []
    start_cursor: str | None = None

    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            payload: Dict[str, Any] = {"page_size": PAGE_SIZE}
            if filter_block:
                payload["filter"] = filter_block
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


async def _fetch_page_title(page_id: str) -> str:
    headers = _headers()
    url = f"https://api.notion.com/v1/pages/{page_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        title = _extract_title_generic(data.get("properties") or {})
        return title or page_id


async def _resolve_titles(page_ids: List[str]) -> Dict[str, str]:
    unique_ids = [pid for pid in dict.fromkeys(page_ids) if pid]
    if not unique_ids:
        return {}
    results = await asyncio.gather(*(_fetch_page_title(pid) for pid in unique_ids), return_exceptions=True)
    resolved: Dict[str, str] = {}
    for pid, result in zip(unique_ids, results):
        if isinstance(result, Exception):
            resolved[pid] = pid
        else:
            resolved[pid] = result or pid
    return resolved


def _asset_prefix(asset_id: str) -> str:
    return (asset_id or "")[:3].upper()


async def fetch_assets_schema() -> Dict[str, Any]:
    db_id = Config.ASSETS_DB_ID
    if not db_id:
        raise RuntimeError("Missing ASSETS_DB_ID")
    headers = _headers()
    url = f"https://api.notion.com/v1/databases/{db_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    return data.get("properties") or {}


async def update_asset_page(page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    if not page_id:
        raise ValueError("Missing asset page_id")
    headers = _headers()
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"properties": properties}
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def fetch_assets_for_location(location_page_id: str) -> List[Dict[str, Any]]:
    if not location_page_id:
        return []
    filter_block = {"property": "LocationsMasterID", "relation": {"contains": location_page_id}}
    pages = await _query_assets(filter_block=filter_block)

    assets: List[Dict[str, Any]] = []
    production_ids: List[str] = []
    source_production_ids: List[str] = []

    for page in pages:
        props = page.get("properties") or {}
        asset_id = _title(props, "Asset ID")
        production_rel = _relation_ids(props, "ProductionID")
        source_rel = _relation_ids(props, "Source Production")
        production_ids.extend(production_rel)
        source_production_ids.extend(source_rel)

        assets.append(
            {
                "asset_id": asset_id,
                "asset_prefix": _asset_prefix(asset_id),
                "asset_name": _rich_text(props, "Asset Name"),
                "asset_type": _select(props, "Asset Type"),
                "asset_categories": _multi_select(props, "Asset Category"),
                "external_url": _url(props, "External URL"),
                "production_ids": production_rel,
                "prod_loc_ids": _relation_ids(props, "ProdLocID"),
                "locations_master_ids": _relation_ids(props, "LocationsMasterID"),
                "source_production_ids": source_rel,
                "notes": _rich_text(props, "Notes"),
                "hazard_types": _multi_select(props, "Hazard Types"),
                "date_taken": _date(props, "Date Taken"),
                "visibility_flag": _select(props, "Visibility Flag"),
                "notion_page_id": page.get("id") or "",
            }
        )

    title_map = await _resolve_titles(production_ids + source_production_ids)
    for asset in assets:
        asset["production_names"] = [title_map.get(pid, pid) for pid in asset.get("production_ids") or []]
        asset["source_production_names"] = [title_map.get(pid, pid) for pid in asset.get("source_production_ids") or []]

    return assets
