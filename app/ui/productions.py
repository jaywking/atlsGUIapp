from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from nicegui import ui

from app.services.api_client import api_url

logger = logging.getLogger(__name__)

ROWS_PER_PAGE = 10
AUTO_REFRESH_SECONDS = 60


def page_content() -> None:
    state: Dict[str, Any] = {
        "rows": [],
        "filtered": [],
        "search": "",
        "page": 0,
        "auto_refresh": False,
    }

    ui.label("Productions").classes("text-xl font-semibold")
    ui.label("Finalized view of Notion productions").classes("text-slate-500 mb-4")

    with ui.row().classes("items-center gap-3 w-full flex-wrap"):
        refresh_button = ui.button("Refresh").classes("bg-blue-500 text-white")
        sync_button = ui.button("Sync to Notion").classes("bg-slate-800 text-white")
        auto_switch = ui.switch("Auto-refresh (60s)").classes("text-sm text-slate-600")
        spinner = ui.spinner(size="md").style("display: none;")
        status_label = ui.label("No data loaded yet.").classes("text-sm text-slate-500 ml-auto")
        dirty_label = ui.label("").classes("text-xs text-amber-600")

    with ui.row().classes("items-center gap-3 w-full flex-wrap"):
        search_input = ui.input(label="Search productions...").props("dense clearable debounce=300").classes("w-72")
        page_info = ui.label("Page 1 of 1").classes("text-sm text-slate-500 ml-auto")
        prev_button = ui.button("Prev").classes("bg-slate-200 text-slate-700")
        next_button = ui.button("Next").classes("bg-slate-200 text-slate-700")

    columns = [
        {"name": "ProductionID", "label": "ProductionID", "field": "ProductionID", "sortable": True},
        {"name": "Name", "label": "Name", "field": "Name", "sortable": True},
        {"name": "Abbreviation", "label": "Abbreviation", "field": "Abbreviation", "sortable": True},
        {"name": "Nickname", "label": "Nickname", "field": "Nickname", "sortable": True},
        {"name": "ProdStatus", "label": "ProdStatus", "field": "ProdStatus", "sortable": True},
        {"name": "ClientPlatform", "label": "Client / Platform", "field": "ClientPlatform", "sortable": True},
        {"name": "ProductionType", "label": "Production Type", "field": "ProductionType", "sortable": True},
        {"name": "Status", "label": "Status", "field": "Status", "sortable": True},
        {"name": "Studio", "label": "Studio", "field": "Studio", "sortable": True},
        {"name": "PPFirstDate", "label": "PPFirstDate", "field": "PPFirstDate", "sortable": True},
        {"name": "PPLastDay", "label": "PPLastDay", "field": "PPLastDay", "sortable": True},
        {"name": "LocationsTable", "label": "Locations Table", "field": "LocationsTable", "sortable": False},
        {"name": "CreatedTime", "label": "Created", "field": "CreatedTime", "sortable": True},
        {"name": "LastEditedTime", "label": "Last Edited", "field": "LastEditedTime", "sortable": True},
    ]

    with ui.element("div").classes("overflow-x-auto w-full"):
        table = (
            ui.table(columns=columns, rows=[], row_key="row_id")
            .classes("w-full text-sm q-table--striped min-w-[1600px]")
            .props('flat wrap-cells square separator="horizontal"')
        )

        # Custom cell for LocationsTable (short link).
        table.add_slot(
            "body-cell-LocationsTable",
            """
            <q-td :props="props">
              <a v-if="props.row.LocationsTable" :href="props.row.LocationsTable" target="_blank">Link</a>
              <span v-else></span>
            </q-td>
            """,
        )

        # Custom cell for ProductionID linking to Notion when available.
        table.add_slot(
            "body-cell-ProductionID",
            """
            <q-td :props="props">
              <a v-if="props.row.NotionURL" :href="props.row.NotionURL" target="_blank">{{ props.row.ProductionID || '' }}</a>
              <span v-else>{{ props.row.ProductionID || '' }}</span>
            </q-td>
            """,
        )

    def set_loading(is_loading: bool) -> None:
        spinner.style("display: inline-block;" if is_loading else "display: none;")
        refresh_button.set_enabled(not is_loading)
        sync_button.set_enabled(not is_loading)

    def update_table_rows(rows: List[Dict[str, Any]]) -> None:
        table.rows = rows
        table.update()

    def apply_filters() -> None:
        search_term = state["search"].lower()
        filtered: List[Dict[str, Any]] = []
        for row in state["rows"]:
            haystack = " ".join(str(v) for v in row.values()).lower()
            if search_term and search_term not in haystack:
                continue
            filtered.append(row)
        state["filtered"] = filtered
        total_pages = max(1, (len(filtered) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE) if filtered else 1
        if state["page"] >= total_pages:
            state["page"] = total_pages - 1
        start = state["page"] * ROWS_PER_PAGE
        end = start + ROWS_PER_PAGE
        update_table_rows(filtered[start:end])
        page_info.set_text(f"Page {state['page'] + 1} of {total_pages} ({len(filtered)} rows)")

    def go_prev(_=None) -> None:
        if state["page"] > 0:
            state["page"] -= 1
            apply_filters()

    def go_next(_=None) -> None:
        total_pages = max(1, (len(state["filtered"]) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE) if state["filtered"] else 1
        if state["page"] < total_pages - 1:
            state["page"] += 1
            apply_filters()

    def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
        row_id = row.get("row_id") or row.get("id") or row.get("ProductionID")
        return {
            "row_id": row_id or "",
            "ProductionID": row.get("ProductionID") or "",
            "NotionURL": row.get("url") or "",
            "Name": row.get("Name") or "",
            "Abbreviation": row.get("Abbreviation") or "",
            "Nickname": row.get("Nickname") or "",
            "ProdStatus": row.get("ProdStatus") or "",
            "ClientPlatform": row.get("ClientPlatform") or "",
            "ProductionType": row.get("ProductionType") or "",
            "Status": row.get("Status") or "",
            "Studio": row.get("Studio") or "",
            "PPFirstDate": row.get("PPFirstDate") or "",
            "PPLastDay": row.get("PPLastDay") or "",
            "LocationsTable": row.get("LocationsTable") or "",
            "CreatedTime": row.get("CreatedTime") or "",
            "LastEditedTime": row.get("LastEditedTime") or "",
        }

    async def fetch_data(show_toast: bool = False, auto_trigger: bool = False, force: bool = False) -> None:
        set_loading(True)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(api_url("/api/productions/fetch"))
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or payload.get("status") != "success":
                raise ValueError(payload.get("message", "Unable to fetch productions"))
            raw_rows = payload.get("data", []) or []
            state["rows"] = [normalize_row(r) for r in raw_rows]
            state["page"] = 0
            apply_filters()
            message = payload.get("message") or f"Loaded {len(state['rows'])} productions"
            status_label.set_text(message)
            if show_toast:
                ui.notify(message, type="positive")
        except Exception as exc:
            logger.exception("Productions fetch failed: %s", exc)
            status_label.set_text(f"Error: {exc}")
            ui.notify(f"Fetch error: {exc}", type="negative")
        finally:
            set_loading(False)

    async def handle_refresh_click(_=None) -> None:
        await fetch_data(show_toast=True, force=True)

    async def sync_now() -> None:
        ui.notify("Sync not implemented in this minimal restore.", type="warning")

    def on_search(value: Optional[str]) -> None:
        state["search"] = (value or "").strip()
        state["page"] = 0
        apply_filters()

    refresh_button.on("click", handle_refresh_click)
    sync_button.on("click", sync_now)
    prev_button.on("click", go_prev)
    next_button.on("click", go_next)
    search_input.on("update:model-value", lambda e: on_search(e.value))
    auto_switch.bind_value(state, "auto_refresh")

    async def do_periodic_fetch():
        await fetch_data(auto_trigger=True)

    async def initial_fetch():
        await fetch_data(show_toast=True)

    ui.timer(AUTO_REFRESH_SECONDS, do_periodic_fetch)
    ui.timer(0.1, initial_fetch, once=True)
