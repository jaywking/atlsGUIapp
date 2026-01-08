from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui.layout import PAGE_HEADER_CLASSES

logger = logging.getLogger(__name__)

ROWS_PER_PAGE = 10


def page_content() -> None:
    state: Dict[str, Any] = {
        "rows": [],
        "filtered": [],
        "search": "",
        "page": 0,
        "sort_by": "",
        "sort_desc": False,
    }

    with ui.column().classes("w-full gap-2"):
        header_classes = PAGE_HEADER_CLASSES.replace("mb-4", "mb-0")
        with ui.row().classes(f"{header_classes} min-h-[52px]"):
            with ui.row().classes("items-center gap-2 flex-wrap w-full"):
                refresh_button = ui.button("Refresh").classes(
                    "bg-blue-500 text-white hover:bg-slate-100 dark:hover:bg-slate-800"
                )
                spinner = ui.spinner(size="md").style("display: none;")
                search_input = ui.input(label="Search productions...").props(
                    "dense clearable debounce=300"
                ).classes("flex-1 min-w-[240px]")
                clear_button = ui.button("Clear", icon="refresh").classes(
                    "bg-slate-200 text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800"
                )

        with ui.row().classes("items-center justify-between w-full gap-2"):
            status_label = ui.label("Loading productions...").classes("text-sm text-slate-500")
            with ui.row().classes("items-center gap-2"):
                prev_button = ui.button("Prev").classes("bg-slate-200 text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800")
                next_button = ui.button("Next").classes("bg-slate-200 text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800")

    columns = [
        {"name": "ProductionName", "label": "Production Name", "field": "ProductionName", "sortable": True},
        {"name": "Code", "label": "Code", "field": "Code", "sortable": True},
        {"name": "Status", "label": "Status", "field": "Status", "sortable": True},
        {"name": "LocationsCount", "label": "Locations", "field": "LocationsCount", "sortable": True},
        {"name": "AssetsCount", "label": "Assets", "field": "AssetsCount", "sortable": True},
        {"name": "actions", "label": "Actions", "field": "ProductionID", "sortable": False},
    ]

    with ui.element("div").classes("overflow-x-auto w-full py-2"):
        table = (
            ui.table(columns=columns, rows=[], row_key="row_id")
            .classes("w-full text-sm q-table--flat min-w-[900px]")
            .props('flat wrap-cells square separator="horizontal" rows-per-page-options="[10]"')
        )
        table.add_slot("no-data", '<div class="hidden"></div>')

        def update_table_rows(rows: List[Dict[str, Any]]) -> None:
            table.rows = rows
            table.update()

        table.update_rows = update_table_rows  # type: ignore[attr-defined]

        table.add_slot(
            "body-cell-ProductionName",
            """
            <q-td :props="props">
              <a
                v-if="props.row.ProductionID"
                :href="`/productions/${props.row.ProductionID}`"
                target="_blank"
                class="text-slate-700 hover:text-slate-900 hover:underline"
              >
                {{ props.row.ProductionName }}
              </a>
              <span v-else>{{ props.row.ProductionName }}</span>
            </q-td>
            """,
        )

        table.add_slot(
            "body-cell-actions",
            """
            <q-td :props="props">
              <a
                v-if="props.row.ProductionID"
                :href="`/productions/${props.row.ProductionID}`"
                target="_blank"
                class="text-slate-700 hover:text-slate-900 hover:underline"
              >
                View Production
              </a>
              <span v-else>--</span>
            </q-td>
            """,
        )

    def set_loading(is_loading: bool) -> None:
        spinner.style("display: inline-block;" if is_loading else "display: none;")
        refresh_button.set_enabled(not is_loading)
        table._props["no-data-label"] = "Loading productions..." if is_loading else ""
        if is_loading:
            status_label.set_text("Loading productions...")
        table.update()

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
                if search_term in _lower(r.get("ProductionName"))
                or search_term in _lower(r.get("Code"))
                or search_term in _lower(r.get("Status"))
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
        status_label.set_text(f"Returned {len(rows)} productions" if rows else "No data available.")
        table._props["no-data-label"] = ""
        table._props["pagination"] = {
            "page": state["page"] + 1,
            "rowsPerPage": ROWS_PER_PAGE,
            "sortBy": sort_by,
            "descending": state.get("sort_desc", False),
            "rowsNumber": len(rows),
        }
        table.update()

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
        production_id = row.get("ProductionID") or ""
        return {
            "row_id": row.get("row_id") or row.get("id") or production_id,
            "ProductionID": production_id,
            "ProductionName": row.get("Name") or production_id or "",
            "Code": row.get("Abbreviation") or "",
            "Status": row.get("Status") or row.get("ProdStatus") or "",
            "LocationsCount": "--",
            "AssetsCount": "--",
        }

    async def fetch_asset_counts() -> Dict[str, int]:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(api_url("/api/assets/list"))
            response.raise_for_status()
            payload = response.json() or {}
            if payload.get("status") != "success":
                raise ValueError(payload.get("message") or "Unable to load assets")
            items = (payload.get("data") or {}).get("items") or []
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unable to load assets for production counts: %s", exc)
            return {}

        counts: Dict[str, int] = {}
        for asset in items:
            for name in asset.get("production_names") or []:
                counts[name] = counts.get(name, 0) + 1
        return counts

    async def fetch_location_counts(production_ids: List[str]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        if not production_ids:
            return counts

        semaphore = asyncio.Semaphore(5)
        async with httpx.AsyncClient(timeout=20.0) as client:
            async def _fetch(pid: str) -> None:
                if not pid:
                    return
                async with semaphore:
                    try:
                        response = await client.get(api_url("/api/productions/detail"), params={"production_id": pid})
                        response.raise_for_status()
                        payload = response.json() or {}
                        if payload.get("status") != "success":
                            return
                        locations = (payload.get("data") or {}).get("locations") or []
                        counts[pid] = len(locations)
                    except Exception:
                        return

            tasks = [asyncio.create_task(_fetch(pid)) for pid in production_ids]
            if tasks:
                await asyncio.gather(*tasks)
        return counts

    async def load_counts() -> None:
        rows = state.get("rows") or []
        production_ids = [row.get("ProductionID") or "" for row in rows]
        asset_counts, location_counts = await asyncio.gather(
            fetch_asset_counts(),
            fetch_location_counts(production_ids),
        )
        for row in rows:
            pid = row.get("ProductionID") or ""
            row["AssetsCount"] = asset_counts.get(pid, 0)
            row["LocationsCount"] = location_counts.get(pid, 0)
        apply_filter()

    async def fetch_data(show_toast: bool = False) -> None:
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
            apply_filter()
            if show_toast:
                ui.notify(payload.get("message") or f"Loaded {len(state['rows'])} productions", type="positive")
        except Exception as exc:
            logger.exception("Productions fetch failed: %s", exc)
            ui.notify(f"Fetch error: {exc}", type="negative")
        finally:
            set_loading(False)

        await load_counts()

    async def handle_refresh_click(_=None) -> None:
        await fetch_data(show_toast=True)

    def on_search(value: Optional[str]) -> None:
        state["search"] = (value or "").strip()
        state["page"] = 0
        apply_filter()

    def clear_filters() -> None:
        state["search"] = ""
        state["page"] = 0
        search_input.set_value("")
        apply_filter()

    refresh_button.on("click", handle_refresh_click)
    prev_button.on("click", go_prev)
    next_button.on("click", go_next)
    clear_button.on("click", lambda _: clear_filters())
    search_input.on_value_change(lambda e: on_search(getattr(e, "value", None)))
    table.on("request", lambda e: handle_table_request(e))

    ui.timer(0.1, lambda: asyncio.create_task(fetch_data(show_toast=True)), once=True)
