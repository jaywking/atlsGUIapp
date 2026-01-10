from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body

from app.services.notion_assets import fetch_all_assets, fetch_asset_by_id, fetch_assets_schema, update_asset_page


router = APIRouter(prefix="/api/assets", tags=["assets"])


def _extract_select_options(prop: Dict[str, Any]) -> List[str]:
    options = prop.get("select", {}).get("options", []) if isinstance(prop, dict) else []
    return [opt.get("name") for opt in options if isinstance(opt, dict) and opt.get("name")]


def _extract_multi_options(prop: Dict[str, Any]) -> List[str]:
    options = prop.get("multi_select", {}).get("options", []) if isinstance(prop, dict) else []
    return [opt.get("name") for opt in options if isinstance(opt, dict) and opt.get("name")]


def _rt(value: str) -> Dict[str, Any]:
    return {"rich_text": [{"text": {"content": value}}]}


def _select(value: Optional[str]) -> Dict[str, Any]:
    return {"select": {"name": value}} if value else {"select": None}


def _multi(values: List[str]) -> Dict[str, Any]:
    return {"multi_select": [{"name": v} for v in values]}


def _date(value: Optional[str]) -> Dict[str, Any]:
    return {"date": {"start": value}} if value else {"date": None}


def _asset_prefix(asset_id: str) -> str:
    return (asset_id or "")[:3].upper()


@router.get("/options")
async def asset_options() -> Dict[str, Any]:
    schema = await fetch_assets_schema()
    hazard_prop = schema.get("Hazard Types") or {}
    category_prop = schema.get("Asset Category") or {}
    visibility_prop = schema.get("Visibility Flag") or {}
    return {
        "status": "success",
        "data": {
            "asset_categories": _extract_multi_options(category_prop),
            "hazard_types": _extract_multi_options(hazard_prop),
            "visibility_flags": ["Visible", "Hidden"],
            "has_asset_categories": bool(category_prop),
            "has_hazard_types": bool(hazard_prop),
            "has_visibility_flag": bool(visibility_prop),
        },
    }


@router.get("/list")
async def list_assets() -> Dict[str, Any]:
    try:
        assets = await fetch_all_assets()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Unable to load assets: {exc}", "data": {"items": []}}
    return {"status": "success", "data": {"items": assets, "total": len(assets)}}


@router.get("/detail")
async def asset_detail(asset_id: str | None = None) -> Dict[str, Any]:
    asset_id = (asset_id or "").strip()
    if not asset_id:
        return {"status": "error", "message": "asset_id is required", "data": {}}
    try:
        asset = await fetch_asset_by_id(asset_id)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Unable to load asset: {exc}", "data": {}}
    if not asset:
        return {"status": "error", "message": f"Asset {asset_id} not found", "data": {}}
    return {"status": "success", "data": {"asset": asset}}


@router.post("/update")
async def update_asset(payload: Dict[str, Any] | None = Body(None)) -> Dict[str, Any]:
    payload = payload or {}
    asset_id = (payload.get("asset_id") or "").strip()
    page_id = (payload.get("page_id") or "").strip()
    if not asset_id or not page_id:
        return {"status": "error", "message": "asset_id and page_id are required"}

    asset_prefix = _asset_prefix(asset_id)
    asset_name = (payload.get("asset_name") or "").strip()
    if not asset_name:
        return {"status": "error", "message": "Asset Name is required", "field": "asset_name"}

    schema = await fetch_assets_schema()
    allowed_categories = _extract_multi_options(schema.get("Asset Category") or {})
    allowed_hazards = _extract_multi_options(schema.get("Hazard Types") or {})

    visibility_provided = "visibility_flag" in payload
    visibility = (payload.get("visibility_flag") or "").strip()
    if visibility_provided and visibility and visibility not in {"Visible", "Hidden"}:
        return {"status": "error", "message": "Visibility Flag must be Visible or Hidden", "field": "visibility_flag"}

    if visibility_provided and visibility == "Hero":
        return {"status": "error", "message": "Visibility Flag cannot be Hero", "field": "visibility_flag"}

    notes = payload.get("notes") or ""
    hazard_types = payload.get("hazard_types") or []
    asset_categories = payload.get("asset_categories") or []
    date_taken = (payload.get("date_taken") or "").strip() or None

    if hazard_types and not all(h in allowed_hazards for h in hazard_types):
        return {"status": "error", "message": "Hazard Types contain invalid values", "field": "hazard_types"}
    if asset_categories and not all(c in allowed_categories for c in asset_categories):
        return {"status": "error", "message": "Asset Category contains invalid values", "field": "asset_categories"}

    properties: Dict[str, Any] = {"Asset Name": _rt(asset_name)}
    if "Notes" in schema:
        properties["Notes"] = _rt(str(notes))

    if asset_prefix == "PIC":
        if "Hazard Types" in schema:
            properties["Hazard Types"] = _multi(hazard_types)
        if "Date Taken" in schema:
            properties["Date Taken"] = _date(date_taken)
        if visibility_provided and "Visibility Flag" in schema:
            properties["Visibility Flag"] = _select(visibility or None)
    elif asset_prefix == "AST":
        if "Asset Category" in schema:
            properties["Asset Category"] = _multi(asset_categories)
        if "Hazard Types" in schema and payload.get("hazard_types") is not None:
            properties["Hazard Types"] = _multi(hazard_types)
        if visibility_provided and "Visibility Flag" in schema:
            properties["Visibility Flag"] = _select(visibility or None)
    elif asset_prefix == "FOL":
        pass
    else:
        return {"status": "error", "message": f"Unsupported asset type: {asset_prefix}"}

    try:
        await update_asset_page(page_id, properties)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Unable to update asset: {exc}"}

    return {"status": "success", "message": "Asset updated.", "data": {"asset_id": asset_id}}
