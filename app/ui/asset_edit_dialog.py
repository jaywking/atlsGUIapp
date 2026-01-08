from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, Optional

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui.asset_diagnostics import asset_prefix


async def _load_asset_options(cache: Dict[str, Any]) -> Dict[str, Any]:
    cached = cache.get("asset_options")
    if isinstance(cached, dict):
        return cached
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(api_url("/api/assets/options"))
        response.raise_for_status()
        payload = response.json() or {}
        if payload.get("status") != "success":
            raise ValueError(payload.get("message") or "Unable to load asset options")
        options = payload.get("data") or {}
    except Exception:
        options = {
            "asset_categories": [],
            "hazard_types": [],
            "visibility_flags": ["Visible", "Hidden"],
            "has_asset_categories": False,
            "has_hazard_types": False,
            "has_visibility_flag": False,
        }
    cache["asset_options"] = options
    return options


def build_asset_edit_dialog(on_saved: Callable[[], Awaitable[None]]) -> Callable[[Dict[str, Any]], Awaitable[None]]:
    state: Dict[str, Any] = {"asset_options": None, "editing_asset": None}

    with ui.dialog() as edit_dialog, ui.card().classes("min-w-[420px]"):
        ui.label("Edit Asset").classes("text-lg font-semibold")
        edit_asset_label = ui.label("").classes("text-sm text-slate-500")

        name_input = ui.input(label="Asset Name").classes("w-full")
        name_error = ui.label("").classes("text-xs text-red-600")

        notes_input = ui.textarea(label="Notes").classes("w-full h-28")
        notes_error = ui.label("").classes("text-xs text-red-600")

        hazard_block = ui.column().classes("w-full gap-1")
        with hazard_block:
            hazard_select = ui.select([], label="Hazard Types", multiple=True).props("use-input fill-input clearable")
            hazard_error = ui.label("").classes("text-xs text-red-600")

        date_block = ui.column().classes("w-full gap-1")
        with date_block:
            date_input = ui.input(label="Date Taken").props("type=date clearable").classes("w-full")
            date_error = ui.label("").classes("text-xs text-red-600")

        visibility_block = ui.column().classes("w-full gap-1")
        with visibility_block:
            visibility_select = ui.select(["Visible", "Hidden"], label="Visibility Flag").props("clearable").classes("w-full")
            visibility_error = ui.label("").classes("text-xs text-red-600")

        visibility_locked = ui.label("").classes("text-xs text-slate-500")

        categories_block = ui.column().classes("w-full gap-1")
        with categories_block:
            categories_select = ui.select([], label="Asset Category", multiple=True).props("use-input fill-input clearable")
            categories_error = ui.label("").classes("text-xs text-red-600")

        error_banner = ui.label("").classes("text-sm text-red-600")

        with ui.row().classes("items-center gap-2 mt-2"):
            save_btn = ui.button("Save").classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1")
            cancel_btn = ui.button("Cancel").props("flat")

    def _reset_errors() -> None:
        for label in [name_error, notes_error, hazard_error, date_error, visibility_error, categories_error, error_banner]:
            label.set_text("")

    async def open_edit(asset: Dict[str, Any]) -> None:
        options = await _load_asset_options(state)
        state["editing_asset"] = asset
        asset_id = asset.get("asset_id") or ""
        edit_asset_label.set_text(asset_id)

        name_input.set_value(asset.get("asset_name") or "")
        notes_input.set_value(asset.get("notes") or "")
        hazard_select.options = options.get("hazard_types") or []
        hazard_select.set_value(asset.get("hazard_types") or [])
        categories_select.options = options.get("asset_categories") or []
        categories_select.set_value(asset.get("asset_categories") or [])
        date_input.set_value(asset.get("date_taken") or "")
        visibility_select.set_value(asset.get("visibility_flag") or None)

        prefix = asset_prefix(asset_id)
        hazard_block.set_visibility(prefix in {"PIC", "AST"} and options.get("has_hazard_types"))
        categories_block.set_visibility(prefix == "AST" and options.get("has_asset_categories"))
        date_block.set_visibility(prefix == "PIC")

        if prefix in {"PIC", "AST"} and options.get("has_visibility_flag"):
            if (asset.get("visibility_flag") or "") == "Hero":
                visibility_block.set_visibility(False)
                visibility_locked.set_text("Visibility: Hero (locked)")
                visibility_locked.set_visibility(True)
            else:
                visibility_locked.set_visibility(False)
                visibility_block.set_visibility(True)
        else:
            visibility_block.set_visibility(False)
            visibility_locked.set_visibility(False)

        _reset_errors()
        edit_dialog.open()

    async def save_edit() -> None:
        asset = state.get("editing_asset") or {}
        asset_id = asset.get("asset_id") or ""
        prefix = asset_prefix(asset_id)
        options = state.get("asset_options") or {}
        _reset_errors()

        name_value = (name_input.value or "").strip()
        if not name_value:
            name_error.set_text("Asset Name is required.")
            return

        visibility_value = (visibility_select.value or "").strip()
        if visibility_block.visible and visibility_value not in {"Visible", "Hidden", ""}:
            visibility_error.set_text("Visibility must be Visible or Hidden.")
            return

        hazard_values = hazard_select.value or []
        category_values = categories_select.value or []
        allowed_hazards = options.get("hazard_types") or []
        allowed_categories = options.get("asset_categories") or []

        if hazard_values and not all(v in allowed_hazards for v in hazard_values):
            hazard_error.set_text("Select valid hazard types.")
            return
        if category_values and not all(v in allowed_categories for v in category_values):
            categories_error.set_text("Select valid categories.")
            return

        payload: Dict[str, Any] = {
            "page_id": asset.get("notion_page_id"),
            "asset_id": asset_id,
            "asset_name": name_value,
            "notes": notes_input.value or "",
        }

        if prefix == "PIC":
            if hazard_block.visible:
                payload["hazard_types"] = hazard_values
            payload["date_taken"] = date_input.value or ""
            if visibility_block.visible:
                payload["visibility_flag"] = visibility_value
        elif prefix == "AST":
            if categories_block.visible:
                payload["asset_categories"] = category_values
            if hazard_block.visible:
                payload["hazard_types"] = hazard_values
            if visibility_block.visible:
                payload["visibility_flag"] = visibility_value
        elif prefix == "FOL":
            pass
        else:
            error_banner.set_text("Unsupported asset type.")
            return

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(api_url("/api/assets/update"), json=payload)
            response.raise_for_status()
            result = response.json() or {}
            if result.get("status") != "success":
                raise ValueError(result.get("message") or "Unable to update asset")
        except Exception:
            ui.notify("Unable to update asset. Please try again.", type="warning", position="top")
            return

        ui.notify("Asset updated.", type="positive", position="top")
        edit_dialog.close()
        await on_saved()

    save_btn.on("click", lambda e: asyncio.create_task(save_edit()))
    cancel_btn.on("click", lambda e: edit_dialog.close())

    return open_edit
