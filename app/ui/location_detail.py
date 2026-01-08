from __future__ import annotations

import asyncio
from typing import Any, Dict, List
from urllib.parse import urlparse

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui.layout import PAGE_HEADER_CLASSES


def _render_kv(label: str, value: str) -> None:
    with ui.row().classes("w-full items-start gap-2"):
        ui.label(label).classes("text-sm text-slate-500 w-48 shrink-0")
        ui.label(value or "--").classes("text-sm text-slate-900")


def _render_kv_if(label: str, value: str | None) -> None:
    if value is None:
        return
    if isinstance(value, str) and not value.strip():
        return
    _render_kv(label, str(value))


def _asset_prefix(asset_id: str) -> str:
    return (asset_id or "")[:3].upper()


def _render_section_header(title: str) -> None:
    ui.label(title).classes("text-lg font-semibold")


def _thumbnail_html(url: str, alt: str) -> str:
    safe_url = url.replace('"', "")
    safe_alt = alt.replace('"', "")
    return (
        f'<a href="{safe_url}" target="_blank" rel="noopener">'
        f'<img src="{safe_url}" alt="{safe_alt}" class="w-20 h-20 object-cover rounded" />'
        "</a>"
    )


def _is_valid_url(value: str) -> bool:
    if not value:
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def _asset_diagnostics_base(asset: Dict[str, Any], hero_conflicts: set[str]) -> List[Dict[str, str]]:
    diags: List[Dict[str, str]] = []
    asset_id = asset.get("asset_id") or ""
    prefix = _asset_prefix(asset_id)
    production_ids = asset.get("production_ids") or []
    prod_loc_ids = asset.get("prod_loc_ids") or []
    master_ids = asset.get("locations_master_ids") or []

    # Missing or weak context
    if prefix == "PIC" and production_ids and not master_ids:
        diags.append({"severity": "INFO", "label": "Missing LocationsMasterID"})
    if prefix == "PIC" and production_ids and not prod_loc_ids:
        diags.append({"severity": "INFO", "label": "Missing ProdLocID"})
    if prefix == "FOL" and not prod_loc_ids:
        diags.append({"severity": "INFO", "label": "Missing ProdLocID"})

    # Metadata gaps
    if prefix == "PIC" and not (asset.get("asset_name") or "").strip():
        diags.append({"severity": "CHECK", "label": "Missing Asset Name"})
    if prefix == "PIC" and not (asset.get("notes") or "").strip():
        diags.append({"severity": "INFO", "label": "Missing Notes"})
    if prefix == "PIC" and not (asset.get("hazard_types") or []):
        diags.append({"severity": "INFO", "label": "No Hazard Types"})
    if prefix == "AST" and not (asset.get("asset_categories") or []):
        diags.append({"severity": "CHECK", "label": "No Asset Category"})

    # Visibility inconsistencies
    if asset_id and asset_id in hero_conflicts:
        diags.append({"severity": "WARNING", "label": "Multiple Hero photos for location"})

    # External URL issues
    external_url = (asset.get("external_url") or "").strip()
    if not external_url:
        diags.append({"severity": "WARNING", "label": "Missing External URL"})
    elif not _is_valid_url(external_url):
        diags.append({"severity": "WARNING", "label": "Invalid External URL"})

    return diags


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
    state: Dict[str, Any] = {"location": None, "productions": [], "assets": [], "assets_warning": "", "asset_options": None}

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

    async def _load_asset_options() -> Dict[str, Any]:
        cached = state.get("asset_options")
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
            options = {"asset_categories": [], "hazard_types": [], "visibility_flags": ["Visible", "Hidden"], "has_asset_categories": False, "has_hazard_types": False, "has_visibility_flag": False}
        state["asset_options"] = options
        return options

    def _reset_edit_errors() -> None:
        for label in [name_error, notes_error, hazard_error, date_error, visibility_error, categories_error, error_banner]:
            label.set_text("")

    async def open_edit(asset: Dict[str, Any]) -> None:
        options = await _load_asset_options()
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

        prefix = _asset_prefix(asset_id)
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

        _reset_edit_errors()
        edit_dialog.open()

    async def save_edit() -> None:
        asset = state.get("editing_asset") or {}
        asset_id = asset.get("asset_id") or ""
        prefix = _asset_prefix(asset_id)
        options = state.get("asset_options") or {}
        _reset_edit_errors()

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
        await load_detail()

    save_btn.on("click", lambda e: asyncio.create_task(save_edit()))
    cancel_btn.on("click", lambda e: edit_dialog.close())

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

        hero_conflicts: set[str] = set()
        hero_by_location: Dict[str, List[str]] = {}
        for asset in assets:
            asset_id = asset.get("asset_id") or ""
            if _asset_prefix(asset_id) != "PIC":
                continue
            if (asset.get("visibility_flag") or "") != "Hero":
                continue
            for loc_id in asset.get("locations_master_ids") or []:
                hero_by_location.setdefault(loc_id, []).append(asset_id)
        for loc_id, asset_ids in hero_by_location.items():
            if len(asset_ids) > 1:
                hero_conflicts.update(asset_ids)

        base_diags: Dict[str, List[Dict[str, str]]] = {}
        for asset in assets:
            asset_id = asset.get("asset_id") or ""
            base_diags[asset_id] = _asset_diagnostics_base(asset, hero_conflicts)

        surfaced_assets: set[str] = set()
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
            _render_section_header("Hero Photo")
            hero_asset = next(
                (
                    asset
                    for asset in assets
                    if _asset_prefix(asset.get("asset_id")) == "PIC" and asset.get("visibility_flag") == "Hero"
                ),
                None,
            )
            # TODO: add explicit hero replacement action once admin UI is approved.
            if hero_asset and hero_asset.get("external_url"):
                ui.html(_thumbnail_html(hero_asset["external_url"], hero_asset.get("asset_name") or "Hero Photo"))
                hero_id = hero_asset.get("asset_id") or ""
                hero_diags = list(base_diags.get(hero_id) or [])
                if (hero_asset.get("visibility_flag") or "") == "Hidden":
                    hero_diags.append({"severity": "CHECK", "label": "Hidden asset surfaced"})
                _render_diagnostics(hero_diags)
                if hero_id:
                    surfaced_assets.add(hero_id)
                    if hero_diags:
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
            _render_section_header("Core Location Information")
            _render_kv_if("Location Name", loc.get("location_name") or "")
            _render_kv_if("Practical Name", loc.get("practical_name") or "")
            _render_kv_if("Full Address", loc.get("full_address") or "")
            _render_kv_if("Address1", loc.get("address1") or "")
            _render_kv_if("Address2", loc.get("address2") or "")
            _render_kv_if("Address3", loc.get("address3") or "")
            _render_kv_if("City", loc.get("city") or "")
            _render_kv_if("State", loc.get("state") or "")
            _render_kv_if("Zip", loc.get("zip") or "")
            _render_kv_if("Country", loc.get("country") or "")
            _render_kv_if("County", loc.get("county") or "")
            _render_kv_if("Borough", loc.get("borough") or "")
            _render_kv_if("Latitude", loc.get("latitude"))
            _render_kv_if("Longitude", loc.get("longitude"))
            _render_kv_if("Place ID", loc.get("place_id") or "")
            _render_kv_if("Place Types", ", ".join(loc.get("place_types") or []))
            _render_kv_if("Status", loc.get("status") or "")
            _render_kv_if("Location Op Status", loc.get("location_op_status") or "")

        folder_section.clear()
        with folder_section:
            _render_section_header("Photo Folders (by Production)")
            folder_assets = [
                asset
                for asset in assets
                if _asset_prefix(asset.get("asset_id")) == "FOL" and "Locations" in (asset.get("asset_categories") or [])
            ]
            photo_assets = [
                asset for asset in assets if _asset_prefix(asset.get("asset_id")) == "PIC"
            ]
            if not folder_assets:
                ui.label("No photo folders linked for this location.").classes("text-sm text-slate-500")
            else:
                for folder in folder_assets:
                    production_name = (folder.get("production_names") or folder.get("production_ids") or ["Production"])[0]
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
                        folder_diags = list(base_diags.get(folder_id) or [])
                        if (folder.get("visibility_flag") or "") == "Hidden":
                            folder_diags.append({"severity": "CHECK", "label": "Hidden asset surfaced"})
                        _render_diagnostics(folder_diags)
                        if folder_id:
                            surfaced_assets.add(folder_id)
                            if folder_diags:
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
                                    ui.html(_thumbnail_html(photo["external_url"], photo.get("asset_name") or "Photo"))

        promoted_section.clear()
        with promoted_section:
            visible_assets = [
                asset
                for asset in assets
                if _asset_prefix(asset.get("asset_id")) == "PIC" and asset.get("visibility_flag") == "Visible"
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
                    with ui.row().classes("w-full gap-4 items-start"):
                        if asset.get("external_url"):
                            ui.html(_thumbnail_html(asset["external_url"], asset.get("asset_name") or "Photo"))
                        with ui.column().classes("gap-1"):
                            with ui.row().classes("items-center gap-2"):
                                ui.label(asset.get("asset_name") or "Photo").classes("text-sm font-semibold text-slate-700")
                                ui.button(
                                    "Edit",
                                    icon="edit",
                                    on_click=lambda e, asset=asset: asyncio.create_task(open_edit(asset)),
                                ).classes("bg-slate-900 text-white hover:bg-slate-800 px-2 py-1 text-xs")
                            promoted_id = asset.get("asset_id") or ""
                            promoted_diags = list(base_diags.get(promoted_id) or [])
                            if (asset.get("visibility_flag") or "") == "Hidden":
                                promoted_diags.append({"severity": "CHECK", "label": "Hidden asset surfaced"})
                            _render_diagnostics(promoted_diags)
                            if promoted_id:
                                surfaced_assets.add(promoted_id)
                                if promoted_diags:
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
            other_assets = [asset for asset in assets if _asset_prefix(asset.get("asset_id")) == "AST"]
            if other_assets:
                _render_section_header("Other Assets (Non-Photo)")
                for asset in other_assets:
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
                            other_diags = list(base_diags.get(other_id) or [])
                            if (asset.get("visibility_flag") or "") == "Hidden":
                                other_diags.append({"severity": "CHECK", "label": "Hidden asset surfaced"})
                            _render_diagnostics(other_diags)
                            if other_id:
                                surfaced_assets.add(other_id)
                                if other_diags:
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
            _render_section_header("Related Productions")
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

    ui.timer(0.1, lambda: asyncio.create_task(load_detail()), once=True)
