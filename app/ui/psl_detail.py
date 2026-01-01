from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui.layout import PAGE_HEADER_CLASSES


def _render_kv(label: str, value: str) -> None:
    with ui.row().classes("w-full items-start gap-2"):
        ui.label(label).classes("text-sm text-slate-500 w-48 shrink-0")
        ui.label(value or "--").classes("text-sm text-slate-900 dark:text-slate-200")


def page_content(production_id: str, master_id: str) -> None:
    title_label = ui.label("PSL Details").classes("text-xl font-semibold")
    subtitle_label = ui.label("").classes("text-sm text-slate-500")

    with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px] items-center justify-between"):
        with ui.column().classes("w-full"):
            title_label
            subtitle_label

    with ui.row().classes("items-center gap-2"):
        loading_spinner = ui.spinner(size="md").props("color=primary")
        status_label = ui.label("Loading PSL details...").classes("text-sm text-slate-500")

    context_block = ui.card().classes("w-full")
    table_block = ui.card().classes("w-full")
    meta_block = ui.expansion("Metadata", icon="info", value=False).classes("w-full")

    async def load_detail() -> None:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    api_url("/api/psl/detail"),
                    params={"production_id": production_id, "master_id": master_id},
                )
            response.raise_for_status()
            payload = response.json() or {}
            if payload.get("status") != "success":
                raise ValueError(payload.get("message") or "PSL not found")
            data = payload.get("data") or {}
        except Exception as exc:  # noqa: BLE001
            loading_spinner.set_visibility(False)
            status_label.set_text(f"PSL not found: {exc}")
            return

        loading_spinner.set_visibility(False)
        status_label.set_text("")

        context = data.get("context") or {}
        rows: List[Dict[str, Any]] = data.get("rows") or []

        production = context.get("production") or {}
        location = context.get("location") or {}
        subtitle_label.set_text(f"{production.get('name', '')} • {location.get('practical_name', '')}".strip(" •"))

        context_block.clear()
        with context_block:
            with ui.row().classes("w-full gap-6 flex-wrap"):
                with ui.column().classes("flex-1 min-w-[260px] gap-2"):
                    _render_kv("Production Name", production.get("name") or "")
                    _render_kv("Production ID", production.get("id") or "")
                with ui.column().classes("flex-1 min-w-[260px] gap-2"):
                    with ui.row().classes("w-full items-start gap-2"):
                        ui.label("Location Master ID").classes("text-sm text-slate-500 w-48 shrink-0")
                        if location.get("master_id"):
                            ui.link(
                                location.get("master_id"),
                                f"/locations/{location.get('master_id')}",
                            ).props("target=_blank").classes("text-sm text-slate-900 hover:underline")
                        else:
                            ui.label("--").classes("text-sm text-slate-900 dark:text-slate-200")
                    _render_kv("Practical Name", location.get("practical_name") or "")
                    _render_kv("Location Name (PSL)", location.get("psl_location_name") or "")
                    _render_kv("Full Address", location.get("full_address") or "")
                    _render_kv(
                        "City / State",
                        f"{location.get('city', '')}, {location.get('state', '')}".strip(", "),
                    )

        table_block.clear()
        with table_block:
            if not rows:
                ui.label("No PSL entries found for this Production and Location.").classes("text-sm text-slate-500")
            else:
                columns = [
                    {"name": "psl_id", "label": "PSL ID", "field": "psl_id", "sortable": True},
                    {"name": "location_name", "label": "Location Name", "field": "location_name", "sortable": True},
                    {"name": "address", "label": "Address", "field": "address", "sortable": False},
                    {"name": "city", "label": "City", "field": "city", "sortable": True},
                    {"name": "state", "label": "State", "field": "state", "sortable": True},
                    {"name": "notes", "label": "Notes", "field": "notes", "sortable": False},
                    {"name": "status", "label": "Status", "field": "status", "sortable": True},
                    {"name": "location_op_status", "label": "Op Status", "field": "location_op_status", "sortable": True},
                ]
                with ui.element("div").classes("w-full overflow-x-auto py-2"):
                    ui.table(columns=columns, rows=rows, row_key="psl_id").classes("w-full text-sm").props(
                        'flat square wrap-cells dense sort-by="psl_id"'
                    )

        meta_block.clear()
        with meta_block:
            if not rows:
                ui.label("No metadata available.").classes("text-sm text-slate-500")
            else:
                for row in rows:
                    ui.label(row.get("psl_id") or "PSL Row").classes("text-sm font-semibold")
                    _render_kv("Created", row.get("created_time") or "")
                    _render_kv("Last Updated", row.get("updated_time") or "")
                    _render_kv("Notion Page ID", row.get("notion_page_id") or "")

    ui.timer(0.1, lambda: asyncio.create_task(load_detail()), once=True)
