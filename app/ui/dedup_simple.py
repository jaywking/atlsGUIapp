from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Request
from nicegui import ui

from app.core.settings import settings
from app.ui.layout import PAGE_HEADER_CLASSES

logger = logging.getLogger(__name__)


def page_content(request: Request) -> None:
    if not settings.DEBUG_ADMIN:
        ui.label("Not authorized.")
        return

    state: Dict[str, Optional[Any]] = {"selected_group_id": None, "preview_data": None, "master_lookup": {}}

    with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px] items-center justify-between"):
        refresh_button = ui.button(
            "Refresh Groups",
        ).classes("px-3 py-1 bg-slate-900 text-white dark:bg-slate-800 hover:bg-slate-800")

    ui.separator()

    status_label = ui.label("Click Refresh Groups to load duplicate groups.").classes("text-sm text-slate-500")

    with ui.row().classes("w-full gap-4 items-start flex-wrap lg:flex-nowrap"):
        with ui.column().classes("w-full lg:w-7/12"):
            with ui.card().classes("w-full shadow-sm border border-slate-200 dark:border-slate-700"):
                ui.label("List Groups").classes("text-lg font-semibold")
                ui.label("Fetch /api/locations/master/dedup?refresh=true to list duplicate groups.").classes(
                    "text-sm text-slate-500"
                )
                group_container = ui.column().classes("w-full gap-3 mt-3")

        with ui.column().classes("w-full lg:w-5/12"):
            with ui.card().classes("w-full shadow-sm border border-slate-200 dark:border-slate-700"):
                ui.label("Preview Merge for Selected Group").classes("text-lg font-semibold")
                selected_label = ui.label("No group selected.").classes("text-sm text-slate-500")
                preview_status = ui.label("").classes("text-sm text-slate-500")
                preview_container = ui.column().classes("w-full mt-2")
                apply_button = ui.button(
                    "Apply Merge",
                    on_click=lambda e=None: _run(apply_merge()),
                ).classes("mt-3 px-3 py-1 bg-amber-600 text-white hover:bg-amber-700")
                apply_button.disable()

    def reset_preview() -> None:
        state["selected_group_id"] = None
        state["preview_data"] = None
        selected_label.set_text("No group selected.")
        preview_status.set_text("Select a group to preview.")
        preview_container.clear()
        with preview_container:
            ui.label("Preview data will appear here after loading a group.").classes("text-sm text-slate-500")
        apply_button.disable()

    async def load_groups() -> None:
        status_label.set_text("Loading duplicate groups...")
        group_container.clear()
        state["master_lookup"] = {}
        try:
            async with httpx.AsyncClient(base_url=str(request.base_url), timeout=30.0) as client:
                response = await client.get("/api/locations/master/dedup?refresh=true")
            response.raise_for_status()
            payload = response.json() or {}
            groups: List[Dict[str, Any]]
            if isinstance(payload, dict):
                groups = payload.get("duplicate_groups") or []
            elif isinstance(payload, list):
                groups = payload
            else:
                groups = []

            if not groups:
                status_label.set_text("No duplicate groups found.")
                reset_preview()
                return

            status_label.set_text(f"Loaded {len(groups)} duplicate groups.")
            for group in groups:
                group_id = group.get("group_id") or group.get("groupId")
                row_count = len(group.get("rows") or [])
                for row in group.get("rows") or []:
                    row_id = row.get("id") or row.get("row_id")
                    if row_id:
                        name = row.get("name") or "Unnamed"
                        address = row.get("address") or ""
                        state["master_lookup"][row_id] = {"name": name, "address": address}
                with group_container:
                    with ui.card().classes(
                        "w-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900"
                    ):
                        with ui.row().classes("w-full items-center justify-between gap-3"):
                            with ui.column().classes("gap-1"):
                                ui.label(f"Group ID: {group_id}").classes("font-semibold")
                                ui.label(f"Records: {row_count}").classes("text-sm text-slate-600 dark:text-slate-300")
                            ui.button(
                                "Preview Merge",
                                on_click=lambda e=None, gid=group_id: _run(load_preview(gid)),
                            ).classes("px-3 py-1 bg-slate-800 text-white hover:bg-slate-900")
            group_container.update()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to load dedup groups")
            status_label.set_text(f"Failed to load groups: {exc}")
            ui.notify(f"Failed to load groups: {exc}", type="negative", position="top")
        finally:
            if not group_container.children:
                reset_preview()

    async def load_preview(group_id: Optional[str]) -> None:
        if not group_id:
            ui.notify("Missing group id for preview.", type="negative", position="top")
            return

        state["selected_group_id"] = group_id
        preview_status.set_text(f"Fetching preview for {group_id}...")
        try:
            async with httpx.AsyncClient(base_url=str(request.base_url), timeout=30.0) as client:
                response = await client.get(f"/api/locations/master/dedup_resolve_preview?group_id={group_id}")
            response.raise_for_status()
            preview_data = response.json() or {}
            state["preview_data"] = preview_data
            selected_label.set_text(f"Selected group: {group_id}")
            preview_status.set_text("Preview loaded.")
            preview_container.clear()
            lookup = state.get("master_lookup") or {}

            def meta_for(master_id: str) -> Dict[str, str]:
                meta = lookup.get(master_id) or {}
                name = meta.get("name") or ""
                address = meta.get("address") or ""
                return {"name": name, "address": address}

            def render_table(rows: List[Dict[str, str]]) -> None:
                table_rows = []
                for r in rows:
                    mid = r.get("id") or ""
                    meta = meta_for(mid)
                    name = meta.get("name") or "Unknown"
                    address = meta.get("address") or ""
                    table_rows.append({"name": name, "details": address})
                if not table_rows:
                    ui.label("None").classes("text-sm text-slate-500")
                    return
                ui.table(
                    columns=[
                        {"name": "name", "label": "LocationsMasterID", "field": "name"},
                        {"name": "details", "label": "Details", "field": "details"},
                    ],
                    rows=table_rows,
                ).props("flat bordered dense wrap-cells").classes("w-full text-sm")

            with preview_container:
                ui.label("Resolved IDs").classes("text-sm font-semibold")

                ui.label("Primary:").classes("text-sm font-semibold mt-2")
                render_table([{"id": preview_data.get("primary_id") or ""}])

                dup_ids = preview_data.get("duplicate_ids") or []
                if dup_ids:
                    ui.label("Duplicates:").classes("text-sm font-semibold mt-3")
                    render_table([{"id": dup} for dup in dup_ids])

                prod_updates = preview_data.get("prod_loc_updates") or []
                if prod_updates:
                    ui.label("Production links to rewrite").classes("text-sm font-semibold mt-3")
                    prod_rows: List[Dict[str, str]] = []
                    for idx, upd in enumerate(prod_updates, start=1):
                        target_meta = meta_for(upd.get("new_master_id") or "")
                        target_display = target_meta.get("name") or target_meta.get("address") or "Unknown"
                        prod_rows.append({"item": f"Link {idx}", "target": target_display})
                    ui.table(
                        columns=[
                            {"name": "item", "label": "Item", "field": "item"},
                            {"name": "target", "label": "New Master", "field": "target"},
                        ],
                        rows=prod_rows,
                    ).props("flat bordered dense wrap-cells").classes("w-full text-sm")

                delete_ids = preview_data.get("delete_master_ids") or []
                if delete_ids:
                    ui.label("Will archive").classes("text-sm font-semibold mt-3")
                    render_table([{"id": did} for did in delete_ids])

                summary = preview_data.get("summary")
                if summary:
                    ui.label("Summary").classes("text-sm font-semibold mt-3")
                    _render_line(summary)
            apply_button.enable()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to load dedup preview for %s", group_id)
            preview_status.set_text(f"Preview failed: {exc}")
            ui.notify(f"Preview failed: {exc}", type="negative", position="top")
            apply_button.disable()

    async def apply_merge() -> None:
        group_id = state.get("selected_group_id")
        if not group_id:
            ui.notify("Select a group before applying merge.", type="warning", position="top")
            return

        apply_button.disable()
        apply_button.props("loading")
        preview_status.set_text(f"Applying merge for {group_id}...")
        try:
            async with httpx.AsyncClient(base_url=str(request.base_url), timeout=60.0) as client:
                response = await client.post(
                    "/api/locations/master/dedup_resolve_apply",
                    json={"group_id": group_id},
                )
            response.raise_for_status()
            ui.notify("Merge completed.", type="positive", position="top")
            preview_status.set_text("Merge completed.")
            reset_preview()
            await load_groups()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to apply dedup merge for %s", group_id)
            preview_status.set_text(f"Apply failed: {exc}")
            ui.notify(f"Apply failed: {exc}", type="negative", position="top")
            apply_button.enable()
        finally:
            apply_button.props(remove="loading")
            if state.get("selected_group_id"):
                apply_button.enable()
            else:
                apply_button.disable()

    run_task = getattr(ui, "run_task", None)

    def _run(coro):
        if run_task:
            return run_task(coro)
        return asyncio.create_task(coro)

    def _render_line(text: str) -> None:
        with ui.row().classes("items-start gap-2"):
            ui.icon("chevron_right").classes("text-slate-400 text-sm")
            ui.label(text).classes("text-sm text-slate-700 dark:text-slate-200")

    reset_preview()
    refresh_button.on("click", lambda e: _run(load_groups()))
    _run(load_groups())
