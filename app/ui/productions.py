from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui.layout import PAGE_HEADER_CLASSES

logger = logging.getLogger(__name__)

ROWS_PER_PAGE = 10
AUTO_REFRESH_SECONDS = 60


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        text = str(value)
        if text.endswith("Z"):
            text = text.replace("Z", "+00:00")
        return datetime.fromisoformat(text)
    except Exception:
        return None


def _format_date_only(value: Any) -> str:
    dt = _parse_iso_datetime(value)
    if not dt:
        return str(value or "")
    try:
        dt = dt.astimezone()
    except Exception:
        pass
    return dt.date().isoformat()


def _format_local_datetime(value: Any) -> str:
    dt = _parse_iso_datetime(value)
    if not dt:
        return str(value or "")
    try:
        dt = dt.astimezone()
    except Exception:
        pass
    return dt.strftime("%Y-%m-%d %H:%M")


def page_content() -> None:
    state: Dict[str, Any] = {
        "rows": [],
        "filtered": [],
        "search": "",
        "page": 0,
        "auto_refresh": False,
        "sort_by": "",
        "sort_desc": False,
        "prod_status_options": [],
        "status_options": [],
    }

    with ui.row().classes(f"{PAGE_HEADER_CLASSES} atls-header-tight min-h-[52px]"):
        with ui.row().classes("items-center gap-2 flex-wrap"):
            refresh_button = ui.button("Refresh").classes("bg-blue-500 text-white hover:bg-slate-100 dark:hover:bg-slate-800")
            sync_button = ui.button("Sync to Notion").classes("bg-slate-800 text-white hover:bg-slate-900 dark:hover:bg-slate-800")
            auto_switch = ui.switch("Auto-refresh (60s)").classes("text-sm text-slate-600")
            spinner = ui.spinner(size="md").style("display: none;")
            dirty_label = ui.label("").classes("text-xs text-amber-600")
        with ui.row().classes("items-center gap-2 flex-wrap ml-4"):
            add_button = ui.button("Add Production").classes("bg-emerald-600 text-white hover:bg-emerald-700")
            search_input = ui.input(label="Search productions...").props("dense clearable debounce=300").classes("w-72")
            page_info = ui.label("Page 1 of 1").classes("text-sm text-slate-500")
            prev_button = ui.button("Prev").classes("bg-slate-200 text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800")
            next_button = ui.button("Next").classes("bg-slate-200 text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800")

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

    with ui.element("div").classes("overflow-x-auto w-full py-2"):
        table = (
            ui.table(columns=columns, rows=[], row_key="row_id")
            .classes("w-full text-sm q-table--striped min-w-[1600px]")
            .props('flat wrap-cells square separator="horizontal" rows-per-page-options="[10]"')
        )

        def update_table_rows(rows: List[Dict[str, Any]]) -> None:
            table.rows = rows
            table.update()

        table.update_rows = update_table_rows  # type: ignore[attr-defined]

        # Custom cell for LocationsTable (short link).
        table.add_slot(
            "body-cell-LocationsTable",
            """
            <q-td :props="props">
              <a
                v-if="props.row.LocationsTable"
                :href="props.row.LocationsTable"
                target="_blank"
                class="px-2 py-1 rounded inline-block hover:bg-slate-100 dark:hover:bg-slate-800"
              >Link</a>
              <span v-else></span>
            </q-td>
            """,
        )

        # Custom cell for ProductionID linking to Notion when available.
        table.add_slot(
            "body-cell-ProductionID",
            """
            <q-td :props="props">
              <a
                v-if="props.row.NotionURL"
                :href="props.row.NotionURL"
                target="_blank"
                class="px-2 py-1 rounded inline-block hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                {{ props.row.ProductionID || '' }}
              </a>
              <span v-else>{{ props.row.ProductionID || '' }}</span>
            </q-td>
            """,
        )

    def set_loading(is_loading: bool) -> None:
        spinner.style("display: inline-block;" if is_loading else "display: none;")
        refresh_button.set_enabled(not is_loading)
        sync_button.set_enabled(not is_loading)

    def _lower(value: Any) -> str:
        try:
            return str(value or "").lower()
        except Exception:
            return ""

    def apply_filter() -> None:
        rows = list(state.get("rows") or [])
        search_term = _lower(state.get("search"))
        if search_term:
            rows = [
                r for r in rows
                if search_term in _lower(r.get("ProductionName") or r.get("Name"))
                or search_term in _lower(r.get("Abbreviation"))
                or search_term in _lower(r.get("Nickname"))
                or search_term in _lower(r.get("ClientPlatform"))
                or search_term in _lower(r.get("Studio"))
                or search_term in _lower(r.get("ProdStatus"))
        ]
        state["filtered"] = rows

        sort_by = state.get("sort_by") or ""
        if sort_by:
            try:
                rows.sort(key=lambda r: (str(r.get(sort_by) or "")).lower(), reverse=state.get("sort_desc", False))
            except Exception:
                pass

        total_pages = max(1, (len(rows) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE) if rows else 1
        if state["page"] >= total_pages:
            state["page"] = total_pages - 1
        start = state["page"] * ROWS_PER_PAGE
        end = start + ROWS_PER_PAGE
        visible = rows[start:end]
        table.update_rows(visible)  # type: ignore[attr-defined]
        page_info.set_text(f"Page {state['page'] + 1} of {total_pages} ({len(rows)} rows)")
        table._props["pagination"] = {
            "page": state["page"] + 1,
            "rowsPerPage": ROWS_PER_PAGE,
            "sortBy": sort_by,
            "descending": state.get("sort_desc", False),
            "rowsNumber": len(rows),
        }
        table.update()

    def apply_filters() -> None:
        """Alias for apply_filter to align with expected handler naming."""
        apply_filter()

    def go_prev(_=None) -> None:
        if state["page"] > 0:
            state["page"] -= 1
            apply_filter()

    def go_next(_=None) -> None:
        total_pages = max(1, (len(state["filtered"]) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE) if state["filtered"] else 1
        if state["page"] < total_pages - 1:
            state["page"] += 1
            apply_filter()

    def handle_table_request(event) -> None:
        pagination = (event.args or {}).get("pagination") or {}
        state["sort_by"] = pagination.get("sortBy") or ""
        state["sort_desc"] = bool(pagination.get("descending"))
        page = pagination.get("page")
        if page is not None:
            try:
                state["page"] = max(0, int(page) - 1)
            except Exception:
                pass
        apply_filter()

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
            "CreatedTime": _format_date_only(row.get("CreatedTime")),
            "LastEditedTime": _format_local_datetime(row.get("LastEditedTime")),
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
            normalized = [normalize_row(r) for r in raw_rows]
            state["rows"] = normalized
            state["page"] = 0
            apply_filters()
            message = payload.get("message") or f"Loaded {len(state['rows'])} productions"
            if show_toast:
                ui.notify(message, type="positive")
        except Exception as exc:
            logger.exception("Productions fetch failed: %s", exc)
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
    search_input.on_value_change(lambda e: on_search(getattr(e, "value", None)))
    auto_switch.bind_value(state, "auto_refresh")
    table.on("request", lambda e: handle_table_request(e))

    with ui.dialog() as add_dialog, ui.card().classes("min-w-[360px]"):
        ui.label("Create Production").classes("text-lg font-semibold mb-2")
        code_input = ui.input(label="Abbreviation", placeholder="e.g. TGD").classes("w-full").props("clearable")
        name_input = ui.input(label="Production Name", placeholder="e.g. The Great Demo").classes("w-full").props("clearable")
        nickname_input = ui.input(label="Nickname", placeholder="Optional").classes("w-full").props("clearable")
        prod_status_select = ui.select(label="ProdStatus", options=[""], value="").classes("w-full").props("clearable")
        client_platform_input = ui.input(label="Client / Platform", placeholder="Optional").classes("w-full").props("clearable")
        production_type_input = ui.input(label="Production Type", placeholder="Optional").classes("w-full").props("clearable")
        studio_input = ui.input(label="Studio", placeholder="Optional").classes("w-full").props("clearable")
        error_label = ui.label("").classes("text-sm text-red-600")
        with ui.row().classes("items-center gap-2 mt-2"):
            create_btn = ui.button("Create", color="primary")
            cancel_btn = ui.button("Cancel").props("flat")

    def reset_add_dialog() -> None:
        code_input.set_value("")
        name_input.set_value("")
        nickname_input.set_value("")
        prod_status_select.set_value("")
        client_platform_input.set_value("")
        production_type_input.set_value("")
        studio_input.set_value("")
        error_label.set_text("")
        create_btn.set_enabled(True)
        cancel_btn.set_enabled(True)
        code_input.props(remove="readonly")
        name_input.props(remove="readonly")
        nickname_input.props(remove="readonly")
        prod_status_select.props(remove="readonly")
        client_platform_input.props(remove="readonly")
        production_type_input.props(remove="readonly")
        studio_input.props(remove="readonly")

    def set_add_loading(is_loading: bool) -> None:
        create_btn.set_enabled(not is_loading)
        cancel_btn.set_enabled(not is_loading)
        if is_loading:
            create_btn.props("loading")
            code_input.props("readonly")
            name_input.props("readonly")
            nickname_input.props("readonly")
            prod_status_select.props("readonly")
            client_platform_input.props("readonly")
            production_type_input.props("readonly")
            studio_input.props("readonly")
        else:
            create_btn.props(remove="loading")
            code_input.props(remove="readonly")
            name_input.props(remove="readonly")
            nickname_input.props(remove="readonly")
            prod_status_select.props(remove="readonly")
            client_platform_input.props(remove="readonly")
            production_type_input.props(remove="readonly")
            studio_input.props(remove="readonly")

    async def load_option_lists() -> None:
        error_label.set_text("")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(api_url("/api/productions/options"))
            data = response.json()
            if response.status_code != 200 or not isinstance(data, dict) or data.get("status") != "ok":
                raise ValueError(data.get("message") if isinstance(data, dict) else "Request failed")
            prod_opts = [opt for opt in (data.get("prod_status_options") or []) if isinstance(opt, str)]
            status_opts = [opt for opt in (data.get("status_options") or []) if isinstance(opt, str)]
            prod_status_select.options = [""] + prod_opts
            prod_status_select.update()
        except Exception as exc:
            logger.exception("Failed to load production options: %s", exc)
            prod_status_select.options = [""]
            prod_status_select.update()
            error_label.set_text("Failed to load Notion options; you can still type custom values.")

    async def submit_create(_=None) -> None:
        error_label.set_text("")
        code = (code_input.value or "").strip()
        name = (name_input.value or "").strip()
        if not code or not name:
            error_label.set_text("Abbreviation and Name are required.")
            return
        code = code.upper()
        code_input.set_value(code)
        set_add_loading(True)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url("/api/productions/create"),
                    json={
                        "production_code": code,
                        "production_name": name,
                        "nickname": (nickname_input.value or "").strip(),
                        "prod_status": (prod_status_select.value or "").strip(),
                        "client_platform": (client_platform_input.value or "").strip(),
                        "production_type": (production_type_input.value or "").strip(),
                        "studio": (studio_input.value or "").strip(),
                    },
                )
            data = response.json()
            if response.status_code != 200 or not isinstance(data, dict) or data.get("status") != "ok":
                message = data.get("message") if isinstance(data, dict) else "Request failed"
                error_label.set_text(message or "Request failed")
                return
            add_dialog.close()
            await fetch_data(show_toast=True, force=True)
        except Exception as exc:
            logger.exception("Create production failed: %s", exc)
            error_label.set_text("Failed to create production. Please try again.")
        finally:
            set_add_loading(False)

    async def open_add_dialog() -> None:
        reset_add_dialog()
        await load_option_lists()
        add_dialog.open()

    create_btn.on("click", submit_create)
    cancel_btn.on("click", lambda _: add_dialog.close())
    add_button.on("click", open_add_dialog)

    async def do_periodic_fetch():
        await fetch_data(auto_trigger=True)

    async def initial_fetch():
        await fetch_data(show_toast=True)

    ui.timer(AUTO_REFRESH_SECONDS, do_periodic_fetch)
    ui.timer(0.1, initial_fetch, once=True)
