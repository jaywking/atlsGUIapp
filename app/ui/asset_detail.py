from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui.asset_diagnostics import compute_asset_diagnostics, compute_hero_conflicts
from app.ui.asset_edit_dialog import build_asset_edit_dialog
from app.ui.layout import PAGE_HEADER_CLASSES


def _join(values: List[str]) -> str:
    cleaned = [v for v in values if v]
    return ", ".join(cleaned)


def _render_kv(label: str, value: str) -> None:
    with ui.row().classes("w-full items-start gap-2"):
        ui.label(label).classes("text-sm text-slate-500 w-48 shrink-0")
        ui.label(value or "--").classes("text-sm text-slate-900")


def _render_diagnostics(diags: List[Dict[str, str]]) -> None:
    if not diags:
        ui.label("No diagnostics.").classes("text-sm text-slate-500")
        return
    with ui.row().classes("items-center gap-2 flex-wrap"):
        for diag in diags:
            severity = diag.get("severity") or "INFO"
            label = diag.get("label") or ""
            if severity == "WARNING":
                classes = "text-xs px-2 py-0.5 rounded border border-rose-200 text-rose-700 bg-rose-50"
            elif severity == "CHECK":
                classes = "text-xs px-2 py-0.5 rounded border border-amber-200 text-amber-700 bg-amber-50"
            else:
                classes = "text-xs px-2 py-0.5 rounded border border-slate-200 text-slate-600 bg-slate-50"
            ui.label(f"{severity}: {label}").classes(classes)


def page_content(asset_id: str, *, edit: str | None = None) -> None:
    state: Dict[str, Any] = {"asset": None, "auto_edit": bool(edit)}

    title_label = ui.label("Asset Details").classes("text-xl font-semibold")
    subtitle_label = ui.label(asset_id).classes("text-sm text-slate-500")

    with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px] items-center justify-between"):
        with ui.column().classes("w-full"):
            title_label
            subtitle_label

    with ui.row().classes("items-center gap-2"):
        loading_spinner = ui.spinner(size="md").props("color=primary")
        status_label = ui.label("Loading asset details...").classes("text-sm text-slate-500")

    summary_block = ui.expansion("Asset Summary", icon="inventory_2", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    diagnostics_block = ui.expansion("Diagnostics", icon="fact_check", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    metadata_block = ui.expansion("Metadata", icon="edit_note", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    associations_block = ui.expansion("Associations", icon="hub", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    references_block = ui.expansion("References", icon="link", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    actions_block = ui.expansion("Actions", icon="build", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )

    async def load_detail() -> None:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(api_url("/api/assets/detail"), params={"asset_id": asset_id})
            response.raise_for_status()
            payload = response.json() or {}
            if payload.get("status") != "success":
                raise ValueError(payload.get("message") or "Asset not found")
            asset = (payload.get("data") or {}).get("asset") or {}
            state["asset"] = asset
        except Exception as exc:  # noqa: BLE001
            loading_spinner.set_visibility(False)
            status_label.set_text(f"Asset not found: {exc}")
            return

        loading_spinner.set_visibility(False)
        status_label.set_text("")

        asset = state.get("asset") or {}
        title_label.set_text(asset.get("asset_name") or asset.get("asset_id") or "Asset Details")
        subtitle_label.set_text(asset.get("asset_id") or asset_id)

        hero_conflicts = set()
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(api_url("/api/assets/list"))
            response.raise_for_status()
            payload = response.json() or {}
            items = (payload.get("data") or {}).get("items") or []
            hero_conflicts = compute_hero_conflicts(items)
        except Exception:
            hero_conflicts = set()

        diagnostics = compute_asset_diagnostics(asset, hero_conflicts=hero_conflicts)

        summary_block.clear()
        with summary_block:
            _render_kv("Asset ID", asset.get("asset_id") or "")
            _render_kv("Asset Name", asset.get("asset_name") or "")
            _render_kv("Asset Type", asset.get("asset_type") or "")
            _render_kv("Visibility Flag", asset.get("visibility_flag") or "")
            if (asset.get("asset_id") or "").startswith("PIC"):
                hero_status = "Hero" if (asset.get("visibility_flag") or "") == "Hero" else "Not Hero"
                _render_kv("Hero Status", hero_status)

        diagnostics_block.clear()
        with diagnostics_block:
            _render_diagnostics(diagnostics)

        metadata_block.clear()
        with metadata_block:
            ui.button("Edit Asset", icon="edit", on_click=lambda e: asyncio.create_task(open_edit(asset))).classes(
                "bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mb-2"
            )
            _render_kv("Asset Name", asset.get("asset_name") or "")
            _render_kv("Notes", asset.get("notes") or "")
            if asset.get("asset_categories"):
                _render_kv("Asset Category", _join(asset.get("asset_categories") or []))
            if asset.get("hazard_types"):
                _render_kv("Hazard Types", _join(asset.get("hazard_types") or []))
            if asset.get("date_taken"):
                _render_kv("Date Taken", asset.get("date_taken") or "")
            if asset.get("visibility_flag"):
                _render_kv("Visibility Flag", asset.get("visibility_flag") or "")

        associations_block.clear()
        with associations_block:
            _render_kv("Production(s)", _join(asset.get("production_names") or []))
            _render_kv("Locations Master", _join(asset.get("locations_master_names") or []))
            if asset.get("prod_loc_names"):
                _render_kv("ProdLocID", _join(asset.get("prod_loc_names") or []))

        references_block.clear()
        with references_block:
            location_names = asset.get("locations_master_names") or []
            if location_names:
                ui.label("Location Detail pages:").classes("text-sm text-slate-500")
                for name in location_names:
                    ui.link(name, f"/locations/{name}").classes("text-sm text-slate-900 hover:underline")
            if (asset.get("asset_id") or "").startswith("PIC") and (asset.get("visibility_flag") or "") == "Hero":
                hero_targets = _join(asset.get("locations_master_names") or [])
                _render_kv("Hero usage", hero_targets or "--")
            if (asset.get("asset_id") or "").startswith("FOL") and asset.get("prod_loc_names"):
                _render_kv("Folder membership", _join(asset.get("prod_loc_names") or []))
            if not location_names and not asset.get("prod_loc_names"):
                ui.label("No references available.").classes("text-sm text-slate-500")

        actions_block.clear()
        with actions_block:
            ui.button("Edit Asset", icon="edit", on_click=lambda e: asyncio.create_task(open_edit(asset))).classes(
                "bg-slate-900 text-white hover:bg-slate-800 px-3 py-1"
            )
            production_names = asset.get("production_names") or []
            if production_names:
                with ui.row().classes("items-center gap-2 mt-2 flex-wrap"):
                    ui.label("Navigate to Production(s):").classes("text-sm text-slate-500")
                    for name in production_names:
                        ui.link(name, f"/productions/{name}").classes("text-sm text-slate-900 hover:underline")
            location_names = asset.get("locations_master_names") or []
            if location_names:
                with ui.row().classes("items-center gap-2 mt-2 flex-wrap"):
                    ui.label("Navigate to Location(s):").classes("text-sm text-slate-500")
                    for name in location_names:
                        ui.link(name, f"/locations/{name}").classes("text-sm text-slate-900 hover:underline")

        if state.get("auto_edit"):
            state["auto_edit"] = False
            await open_edit(asset)

    open_edit = build_asset_edit_dialog(load_detail)

    ui.timer(0.1, lambda: asyncio.create_task(load_detail()), once=True)
