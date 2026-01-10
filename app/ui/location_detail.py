from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui.asset_diagnostics import (
    asset_prefix,
    compute_asset_diagnostics,
    compute_hero_conflicts,
)
from app.ui.asset_edit_dialog import build_asset_edit_dialog
from app.ui.layout import PAGE_HEADER_CLASSES


def _render_kv(label: str, value: str) -> None:
    with ui.row().classes("w-full items-start gap-2"):
        ui.label(label).classes("text-sm text-slate-500 w-48 shrink-0")
        ui.label(value or "--").classes("text-sm text-slate-900")


def _render_link(label: str, url: str, text: str) -> None:
    if not url:
        return
    with ui.row().classes("w-full items-start gap-2"):
        ui.label(label).classes("text-sm text-slate-500 w-48 shrink-0")
        ui.link(text, url).classes("text-sm text-slate-900 hover:underline").props("target=_blank")


def _render_kv_if(label: str, value: str | None) -> None:
    if value is None:
        return
    if isinstance(value, str) and not value.strip():
        return
    _render_kv(label, str(value))


def _render_section_header(title: str) -> None:
    ui.label(title).classes("text-lg font-semibold")


def _thumbnail_html(url: str, alt: str) -> str:
    safe_url = url.replace('"', "")
    safe_alt = alt.replace('"', "")
    return (
        f'<a href="{safe_url}" target="_blank" rel="noopener">'
        f'<img src="{safe_url}" alt="{safe_alt}" class="w-20 h-20 object-cover rounded" referrerpolicy="no-referrer" />'
        "</a>"
    )


def _render_diagnostics(diags: List[Dict[str, str]]) -> None:
    if not diags:
        return
    with ui.row().classes("items-center gap-2 flex-wrap mt-1"):
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

def page_content(master_id: str) -> None:
    state: Dict[str, Any] = {"location": None, "productions": [], "assets": [], "assets_warning": ""}

    title_label = ui.label("Loading...").classes("text-xl font-semibold")
    subtitle_label = ui.label(master_id).classes("text-sm text-slate-500")

    with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px] items-center justify-between"):
        with ui.column().classes("w-full"):
            title_label
            subtitle_label

    with ui.row().classes("items-center gap-2"):
        loading_spinner = ui.spinner(size="md").props("color=primary")
        status_label = ui.label("Loading location details...").classes("text-sm text-slate-500")
        assets_notice = ui.label("").classes("text-sm text-amber-600")
        assets_notice.set_visibility(False)
        assets_diag_summary = ui.label("").classes("text-sm text-slate-500")
        assets_diag_summary.set_visibility(False)

    hero_section = ui.column().classes("w-full gap-2")
    core_section = ui.column().classes("w-full gap-2")
    folder_section = ui.column().classes("w-full gap-2")
    promoted_section = ui.column().classes("w-full gap-2")
    other_assets_section = ui.column().classes("w-full gap-2")
    related_section = ui.column().classes("w-full gap-2")

    async def load_detail() -> None:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(api_url("/api/locations/detail"), params={"master_id": master_id})
            response.raise_for_status()
            payload = response.json() or {}
            if payload.get("status") != "success":
                raise ValueError(payload.get("message") or "Location not found")
            data = payload.get("data") or {}
            state["location"] = data.get("location") or {}
            state["productions"] = data.get("productions") or []
            state["assets"] = data.get("assets") or []
            state["assets_warning"] = data.get("assets_warning") or ""
        except Exception as exc:  # noqa: BLE001
            loading_spinner.set_visibility(False)
            status_label.set_text(f"Location not found: {exc}")
            return

        loading_spinner.set_visibility(False)
        status_label.set_text("")
        assets_warning = state.get("assets_warning") or ""
        if assets_warning:
            assets_notice.set_text(assets_warning)
            assets_notice.set_visibility(True)
        else:
            assets_notice.set_visibility(False)

        loc = state["location"] or {}
        productions: List[Dict[str, str]] = state["productions"] or []
        assets: List[Dict[str, Any]] = state["assets"] or []

        hero_conflicts = compute_hero_conflicts(assets)
        diag_assets: set[str] = set()

        location_name = loc.get("practical_name") or loc.get("name") or master_id
        title_label.set_text(location_name)
        subtitle_label.set_text(loc.get("master_id") or master_id)

        hero_section.set_visibility(True)
        core_section.set_visibility(True)
        folder_section.set_visibility(True)
        promoted_section.set_visibility(True)
        other_assets_section.set_visibility(True)
        related_section.set_visibility(True)

        hero_section.clear()
        with hero_section:
            hero_asset = next(
                (
                    asset
                    for asset in assets
                    if asset_prefix(asset.get("asset_id")) == "PIC" and asset.get("visibility_flag") == "Hero"
                ),
                None,
            )
            # TODO: add explicit hero replacement action once admin UI is approved.
            if hero_asset and hero_asset.get("external_url"):
                with ui.card().classes("w-full border border-slate-200 rounded-md p-3"):
                    ui.label("Hero Photo").classes("text-sm font-semibold text-slate-700")
                    ui.html(
                        _thumbnail_html(hero_asset["external_url"], hero_asset.get("asset_name") or "Hero Photo"),
                        sanitize=False,
                    )
                    hero_id = hero_asset.get("asset_id") or ""
                    hero_diags = compute_asset_diagnostics(
                        hero_asset,
                        hero_conflicts=hero_conflicts,
                        surfaced_in_location_detail=True,
                    )
                    _render_diagnostics(hero_diags)
                    if hero_id and hero_diags:
                        diag_assets.add(hero_id)
                    ui.button(
                        "Edit",
                        icon="edit",
                        on_click=lambda e, asset=hero_asset: asyncio.create_task(open_edit(asset)),
                    ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mt-2")
            else:
                ui.label("No hero photo selected").classes("text-sm text-slate-500")

        core_section.clear()
        with core_section:
            with ui.card().classes("w-full border border-slate-200 rounded-md p-3"):
                ui.label("Core Location Information").classes("text-sm font-semibold text-slate-700")
                _render_kv_if("Location Name", loc.get("location_name") or "")
                _render_kv_if("Practical Name", loc.get("practical_name") or "")
                _render_kv_if("Full Address", loc.get("full_address") or "")
                _render_link("Google Maps", loc.get("google_maps_url") or "", "Map")
                _render_link("Website", loc.get("website") or "", "Website")
                _render_kv_if("Latitude", loc.get("latitude"))
                _render_kv_if("Longitude", loc.get("longitude"))
                _render_kv_if("Place ID", loc.get("place_id") or "")
                _render_kv_if("Place Types", ", ".join(loc.get("place_types") or []))
                _render_kv_if("Status", loc.get("status") or "")
                _render_kv_if("Location Op Status", loc.get("location_op_status") or "")

        folder_section.clear()
        with folder_section:
            folder_assets = [
                asset
                for asset in assets
                if asset_prefix(asset.get("asset_id")) == "FOL"
                and any(cat in {"Location", "Locations"} for cat in (asset.get("asset_categories") or []))
            ]
            photo_assets = [
                asset for asset in assets if asset_prefix(asset.get("asset_id")) == "PIC"
            ]
            with ui.card().classes("w-full border border-slate-200 rounded-md p-3"):
                ui.label("Photo Folders (by Production)").classes("text-sm font-semibold text-slate-700")
                if not folder_assets:
                    ui.label("No photo folders linked for this location.").classes("text-sm text-slate-500")
                else:
                    for folder in folder_assets:
                        production_name = (folder.get("production_names") or folder.get("production_ids") or ["Production"])[0]
                        with ui.card().classes("w-full border border-slate-200 rounded-md p-3"):
                            with ui.column().classes("w-full gap-2"):
                                ui.label(production_name).classes("text-sm font-semibold text-slate-700")
                                if folder.get("external_url"):
                                    with ui.row().classes("items-center gap-2"):
                                        ui.link("View Photos", folder["external_url"]).props("target=_blank").classes(
                                            "text-sm text-slate-900 hover:underline"
                                        )
                                        ui.button(
                                            "Edit",
                                            icon="edit",
                                            on_click=lambda e, asset=folder: asyncio.create_task(open_edit(asset)),
                                        ).classes("bg-slate-900 text-white hover:bg-slate-800 px-2 py-1 text-xs")
                                folder_id = folder.get("asset_id") or ""
                                folder_diags = compute_asset_diagnostics(
                                    folder,
                                    hero_conflicts=hero_conflicts,
                                    surfaced_in_location_detail=True,
                                )
                                _render_diagnostics(folder_diags)
                                if folder_id and folder_diags:
                                    diag_assets.add(folder_id)
                                prod_ids = folder.get("production_ids") or []
                                thumbnails = []
                                for photo in photo_assets:
                                    if not photo.get("external_url"):
                                        continue
                                    if not prod_ids:
                                        continue
                                    if any(pid in (photo.get("production_ids") or []) for pid in prod_ids):
                                        thumbnails.append(photo)
                                    if len(thumbnails) >= 3:
                                        break
                                if thumbnails:
                                    with ui.row().classes("items-center gap-2"):
                                        for photo in thumbnails:
                                            ui.html(
                                                _thumbnail_html(photo["external_url"], photo.get("asset_name") or "Photo"),
                                                sanitize=False,
                                            )

        promoted_section.clear()
        with promoted_section:
            visible_assets = [
                asset
                for asset in assets
                if asset_prefix(asset.get("asset_id")) == "PIC" and asset.get("visibility_flag") == "Visible"
            ]
            hero_id = hero_asset.get("asset_id") if hero_asset else ""
            promoted_assets = [asset for asset in visible_assets if asset.get("asset_id") != hero_id]
            if promoted_assets:
                _render_section_header("Promoted Photo Assets")
                promoted_assets.sort(
                    key=lambda a: (
                        0 if a.get("hazard_types") else 1,
                        (a.get("asset_name") or "").lower(),
                    )
                )
                for asset in promoted_assets:
                    with ui.card().classes("w-full border border-slate-200 rounded-md p-3"):
                        with ui.row().classes("w-full gap-4 items-start"):
                            if asset.get("external_url"):
                                ui.html(
                                    _thumbnail_html(asset["external_url"], asset.get("asset_name") or "Photo"),
                                    sanitize=False,
                                )
                            with ui.column().classes("gap-1"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.label(asset.get("asset_name") or "Photo").classes("text-sm font-semibold text-slate-700")
                                    ui.button(
                                        "Edit",
                                        icon="edit",
                                        on_click=lambda e, asset=asset: asyncio.create_task(open_edit(asset)),
                                    ).classes("bg-slate-900 text-white hover:bg-slate-800 px-2 py-1 text-xs")
                                promoted_id = asset.get("asset_id") or ""
                                promoted_diags = compute_asset_diagnostics(
                                    asset,
                                    hero_conflicts=hero_conflicts,
                                    surfaced_in_location_detail=True,
                                )
                                _render_diagnostics(promoted_diags)
                                if promoted_id and promoted_diags:
                                    diag_assets.add(promoted_id)
                                if asset.get("notes"):
                                    ui.label(asset["notes"]).classes("text-sm text-slate-600")
                                source_name = (asset.get("source_production_names") or asset.get("production_names") or [""])[0]
                                if source_name:
                                    ui.label(f"Source Production: {source_name}").classes("text-xs text-slate-500")
                                if asset.get("date_taken"):
                                    ui.label(f"Date Taken: {asset['date_taken']}").classes("text-xs text-slate-500")
            else:
                promoted_section.set_visibility(False)

        other_assets_section.clear()
        with other_assets_section:
            other_assets = [asset for asset in assets if asset_prefix(asset.get("asset_id")) == "AST"]
            if other_assets:
                with ui.card().classes("w-full border border-slate-200 rounded-md p-3"):
                    ui.label("Other Assets (Non-Photo)").classes("text-sm font-semibold text-slate-700")
                    for asset in other_assets:
                        with ui.card().classes("w-full border border-slate-200 rounded-md p-3"):
                            with ui.row().classes("w-full items-center justify-between gap-4"):
                                with ui.column().classes("gap-1"):
                                    with ui.row().classes("items-center gap-2"):
                                        ui.label(asset.get("asset_name") or "Asset").classes("text-sm font-semibold text-slate-700")
                                        ui.button(
                                            "Edit",
                                            icon="edit",
                                            on_click=lambda e, asset=asset: asyncio.create_task(open_edit(asset)),
                                        ).classes("bg-slate-900 text-white hover:bg-slate-800 px-2 py-1 text-xs")
                                    other_id = asset.get("asset_id") or ""
                                    other_diags = compute_asset_diagnostics(
                                        asset,
                                        hero_conflicts=hero_conflicts,
                                        surfaced_in_location_detail=True,
                                    )
                                    _render_diagnostics(other_diags)
                                    if other_id and other_diags:
                                        diag_assets.add(other_id)
                                    categories = ", ".join(asset.get("asset_categories") or [])
                                    if categories:
                                        ui.label(f"Category: {categories}").classes("text-xs text-slate-500")
                                    source_name = (asset.get("source_production_names") or asset.get("production_names") or [""])[0]
                                    if source_name:
                                        ui.label(f"Source Production: {source_name}").classes("text-xs text-slate-500")
                                if asset.get("external_url"):
                                    ui.link("Open", asset["external_url"]).props("target=_blank").classes(
                                        "text-sm text-slate-900 hover:underline"
                                    )
            else:
                other_assets_section.set_visibility(False)

        diag_count = len(diag_assets)
        if diag_count > 1:
            assets_diag_summary.set_text(f"{diag_count} assets have checks.")
            assets_diag_summary.set_visibility(True)
        else:
            assets_diag_summary.set_visibility(False)

        related_section.clear()
        with related_section:
            with ui.card().classes("w-full border border-slate-200 rounded-md p-3"):
                ui.label("Related Productions").classes("text-sm font-semibold text-slate-700")
                related_names = {p.get("production_name") or p.get("production_id") for p in productions}
                for asset in assets:
                    for name in asset.get("production_names") or []:
                        related_names.add(name)
                    for name in asset.get("source_production_names") or []:
                        related_names.add(name)
                related_list = sorted([name for name in related_names if name])
                if not related_list:
                    ui.label("No related productions found.").classes("text-sm text-slate-500")
                else:
                    for name in related_list:
                        ui.label(name).classes("text-sm")

    open_edit = build_asset_edit_dialog(load_detail)

    ui.timer(0.1, lambda: asyncio.create_task(load_detail()), once=True)
