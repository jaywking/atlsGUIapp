from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.core.settings import settings
from app.ui.layout import PAGE_HEADER_CLASSES


def _render_kv(label: str, value: str) -> None:
    with ui.row().classes("w-full items-start gap-2"):
        ui.label(label).classes("text-sm text-slate-500 w-48 shrink-0")
        ui.label(value or "--").classes("text-sm text-slate-900 dark:text-slate-200")


def _join_list(values: Any) -> str:
    if not values:
        return ""
    if isinstance(values, list):
        cleaned = [str(v) for v in values if v]
        return ", ".join(cleaned)
    return str(values)


def page_content(production_id: str) -> None:
    state: Dict[str, Any] = {"production": None, "locations": [], "context": {}}

    title_label = ui.label("Production Details").classes("text-xl font-semibold")
    subtitle_label = ui.label(production_id).classes("text-sm text-slate-500")

    with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px] items-center justify-between"):
        with ui.column().classes("w-full"):
            title_label
            subtitle_label

    with ui.row().classes("items-center gap-2"):
        loading_spinner = ui.spinner(size="md").props("color=primary")
        status_label = ui.label("Loading production details...").classes("text-sm text-slate-500")

    summary_block = ui.expansion("Summary", icon="summarize", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    locations_block = ui.expansion("Locations Used", icon="place", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    ops_block = ui.expansion(
        "Production Location Maintenance (Admin)", icon="admin_panel_settings", value=False
    ).classes("w-full").props('header-class="bg-slate-50" content-class="q-pt-none q-pb-none"')
    meta_block = ui.expansion("Metadata", icon="info", value=False).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )

    async def load_detail() -> None:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(api_url("/api/productions/detail"), params={"production_id": production_id})
            response.raise_for_status()
            payload = response.json() or {}
            if payload.get("status") != "success":
                raise ValueError(payload.get("message") or "Production not found")
            data = payload.get("data") or {}
            state["production"] = data.get("production") or {}
            state["locations"] = data.get("locations") or []
            state["context"] = data.get("context") or {}
        except Exception as exc:  # noqa: BLE001
            loading_spinner.set_visibility(False)
            status_label.set_text(f"Production not found: {exc}")
            return

        loading_spinner.set_visibility(False)
        status_label.set_text("")

        production = state["production"] or {}
        locations: List[Dict[str, Any]] = state["locations"] or []
        context: Dict[str, Any] = state["context"] or {}
        locations_db_id = context.get("locations_db_id") or ""
        production_name = context.get("production_name") or production.get("Name") or production_id

        title_label.set_text(production.get("Name") or production_id)
        subtitle_label.set_text("")

        summary_block.clear()
        with summary_block:
            with ui.row().classes("w-full gap-6 flex-wrap"):
                with ui.column().classes("flex-1 min-w-[260px] gap-2"):
                    with ui.row().classes("w-full items-start gap-2"):
                        ui.label("Production ID").classes("text-sm text-slate-500 w-48 shrink-0")
                        prod_id = production.get("ProductionID") or ""
                        notion_url = production.get("url") or ""
                        if prod_id and notion_url:
                            ui.link(prod_id, notion_url).props("target=_blank").classes(
                                "text-sm text-slate-900 hover:underline"
                            )
                        else:
                            ui.label(prod_id or "--").classes("text-sm text-slate-900 dark:text-slate-200")
                    _render_kv("Name", production.get("Name") or "")
                    _render_kv("Abbreviation", production.get("Abbreviation") or "")
                    _render_kv("Nickname", production.get("Nickname") or "")
                    _render_kv("ProdStatus", production.get("ProdStatus") or "")
                with ui.column().classes("flex-1 min-w-[260px] gap-2"):
                    _render_kv("Status", production.get("Status") or "")
                    _render_kv("Client / Platform", production.get("ClientPlatform") or "")
                    _render_kv("Production Type", production.get("ProductionType") or "")
                    _render_kv("Studio", production.get("Studio") or "")

        locations_block.clear()
        with locations_block:
            if not locations:
                ui.label("No Locations linked to this Production.").classes("text-sm text-slate-500")
            else:
                columns = [
                    {
                        "name": "master_id",
                        "label": "Location Master ID",
                        "field": "master_id",
                        "sortable": True,
                        "style": "width: 160px;",
                        "headerStyle": "width: 160px;",
                    },
                    {"name": "psl_location_name", "label": "Location Name (PSL)", "field": "psl_location_name", "sortable": True},
                    {"name": "practical_name", "label": "Practical Name", "field": "practical_name", "sortable": True},
                    {"name": "city", "label": "City", "field": "city", "sortable": True},
                    {"name": "state", "label": "State", "field": "state", "sortable": True},
                    {"name": "place_type", "label": "Place Type", "field": "place_type", "sortable": False},
                    {"name": "map", "label": "Map", "field": "google_maps_url", "sortable": False},
                    {"name": "view_psl", "label": "View PSL", "field": "master_id", "sortable": False},
                ]
                table_rows = []
                for loc in locations:
                    table_rows.append(
                        {
                            "row_id": loc.get("master_id") or "",
                            "master_id": loc.get("master_id") or "",
                            "psl_location_name": loc.get("psl_location_name") or "",
                            "practical_name": loc.get("practical_name") or "",
                            "city": loc.get("city") or "",
                            "state": loc.get("state") or "",
                            "place_type": _join_list(loc.get("place_types")),
                            "google_maps_url": loc.get("google_maps_url") or "",
                            "view_psl_url": f"/psl/{production_id}/{loc.get('master_id') or ''}",
                        }
                    )

                with ui.element("div").classes("w-full overflow-x-auto py-2"):
                    table = (
                        ui.table(columns=columns, rows=table_rows, row_key="row_id")
                        .classes("w-full text-sm")
                        .props('flat square wrap-cells dense sort-by="master_id"')
                    )

                    table.add_slot(
                        "body-cell-master_id",
                        """
                        <q-td :props="props">
                          <a
                            v-if="props.row.master_id"
                            :href="`/locations/${props.row.master_id}`"
                            target="_blank"
                            class="text-slate-700 hover:text-slate-900 hover:underline whitespace-nowrap"
                          >
                            {{ props.row.master_id }}
                          </a>
                          <span v-else>--</span>
                        </q-td>
                        """,
                    )
                    table.add_slot(
                        "body-cell-map",
                        """
                        <q-td :props="props">
                          <a
                            v-if="props.row.google_maps_url"
                            :href="props.row.google_maps_url"
                            target="_blank"
                            class="text-slate-700 hover:text-slate-900 hover:underline"
                          >
                            Map
                          </a>
                          <span v-else>--</span>
                        </q-td>
                        """,
                    )
                    table.add_slot(
                        "body-cell-view_psl",
                        """
                        <q-td :props="props">
                          <a
                            v-if="props.row.view_psl_url && props.row.master_id"
                            :href="props.row.view_psl_url"
                            target="_blank"
                            class="text-slate-700 hover:text-slate-900 hover:underline"
                          >
                            View PSL
                          </a>
                          <span v-else>--</span>
                        </q-td>
                        """,
                    )

        ops_block.clear()
        with ops_block:
            if not settings.DEBUG_ADMIN:
                ui.label("Admin mode is disabled. Enable DEBUG_ADMIN to access production tools.").classes(
                    "text-sm text-slate-500"
                )
            else:
                # Tool: PSL data quality check
                with ui.column().classes("w-full gap-2 mt-2"):
                    ui.button(
                        "Inspect PSL Rows",
                        icon="fact_check",
                        on_click=lambda e: asyncio.create_task(run_inspection()),
                    ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1")
                    ui.label(
                        "Checks PSL rows for missing address data that can break reprocess matching."
                    ).classes("text-sm text-slate-500")
                    inspect_status = ui.label("").classes("text-sm text-slate-500")

                    columns = [
                        {"name": "prod_loc_id", "label": "ProdLocID", "field": "prod_loc_id", "sortable": True},
                        {"name": "location_name", "label": "Location Name", "field": "location_name", "sortable": True},
                        {"name": "missing", "label": "Missing Fields", "field": "missing", "sortable": False},
                        {"name": "notion_url", "label": "Notion", "field": "notion_url", "sortable": False},
                    ]
                    inspect_output = (
                        ui.expansion("Results", icon="table_rows", value=False)
                        .classes("w-full")
                        .props('header-class="q-py-xs" content-class="q-pt-none q-pb-none"')
                    )
                    with inspect_output:
                        table = (
                            ui.table(columns=columns, rows=[], row_key="row_id")
                            .classes("w-full text-sm")
                            .props('flat square wrap-cells dense')
                        )
                        table.add_slot(
                            "body-cell-prod_loc_id",
                            """
                            <q-td :props="props">
                              <a
                                v-if="props.row.notion_url"
                                :href="props.row.notion_url"
                                target="_blank"
                                class="text-slate-700 hover:text-slate-900 hover:underline"
                              >
                                {{ props.row.prod_loc_id }}
                              </a>
                              <span v-else>{{ props.row.prod_loc_id || "--" }}</span>
                            </q-td>
                            """,
                        )
                        table.add_slot(
                            "body-cell-notion_url",
                            """
                            <q-td :props="props">
                              <a
                                v-if="props.row.notion_url"
                                :href="props.row.notion_url"
                                target="_blank"
                                class="text-slate-700 hover:text-slate-900 hover:underline"
                              >
                                Open
                              </a>
                              <span v-else>--</span>
                            </q-td>
                            """,
                        )

                    async def run_inspection() -> None:
                        if not locations_db_id:
                            inspect_status.set_text("No production locations table found.")
                            table.rows = []
                            table.update()
                            return
                        inspect_status.set_text("Inspecting PSL rows...")
                        try:
                            url = api_url("/api/productions/inspect_psl")
                            params = {"db_id": locations_db_id}
                            async with httpx.AsyncClient(timeout=20.0) as client:
                                response = await client.get(url, params=params)
                            response.raise_for_status()
                            payload = response.json() or {}
                            if payload.get("status") != "success":
                                raise ValueError(payload.get("message") or "Inspection failed")
                            rows = payload.get("data") or []
                            table_rows = []
                            for idx, row in enumerate(rows, start=1):
                                table_rows.append(
                                    {
                                        "row_id": f"row-{idx}",
                                        "prod_loc_id": row.get("prod_loc_id") or "--",
                                        "location_name": row.get("location_name") or "--",
                                        "missing": ", ".join(row.get("missing") or []),
                                        "notion_url": row.get("notion_url") or "",
                                    }
                                )
                            table.rows = table_rows
                            table.update()
                            inspect_output.value = True
                            inspect_output.update()
                            if table_rows:
                                inspect_status.set_text(f"Found {len(table_rows)} PSL rows with missing fields.")
                            else:
                                inspect_status.set_text("No missing address fields found.")
                        except Exception as exc:  # noqa: BLE001
                            inspect_status.set_text(f"Inspection failed: {exc}")
                            table.rows = []
                            table.update()

                # Tool: Reprocess Production Locations
                with ui.column().classes("w-full gap-2 mt-4"):
                    reprocess_btn = ui.button(
                        "Re-match Locations (Use Existing Data)",
                        icon="play_arrow",
                        on_click=lambda e: asyncio.create_task(run_reprocess()),
                    ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1")
                    ui.label(
                        "Re-matches this production's locations against Locations Master using current PSL data."
                    ).classes("text-sm text-slate-500")
                    reprocess_timer = {"start": None, "running": False}
                    reprocess_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

                    reprocess_output = (
                        ui.expansion("Output", icon="terminal", value=False)
                        .classes("w-full")
                        .props('header-class="q-py-xs" content-class="q-pt-none q-pb-none"')
                    )
                    with reprocess_output:
                        reprocess_text = ui.textarea(
                            value="Reprocess output will stream here.",
                            placeholder="Streaming progress...",
                        ).classes("w-full text-sm h-36")
                        reprocess_text.props("readonly")

                    def _update_reprocess_timer() -> None:
                        if not reprocess_timer["running"] or reprocess_timer["start"] is None:
                            return
                        elapsed = int(time.time() - reprocess_timer["start"])
                        reprocess_timer_label.set_text(f"Elapsed: {elapsed}s")

                    ui.timer(1.0, _update_reprocess_timer, active=True)

                    async def run_reprocess() -> None:
                        if not locations_db_id:
                            reprocess_text.value = "error: No production locations table found.\n"
                            reprocess_text.update()
                            return
                        reprocess_text.value = "Starting production reprocess...\n"
                        reprocess_text.update()
                        reprocess_output.value = True
                        reprocess_output.update()
                        reprocess_btn.disable()
                        reprocess_timer["start"] = time.time()
                        reprocess_timer["running"] = True
                        reprocess_timer_label.set_text("Elapsed: 0s")
                        try:
                            url = api_url("/api/locations/reprocess_stream")
                            params = {"db_id": locations_db_id}
                            async with httpx.AsyncClient(timeout=None) as client:
                                async with client.stream("GET", url, params=params) as response:
                                    response.raise_for_status()
                                    async for line in response.aiter_lines():
                                        if line is None:
                                            continue
                                        reprocess_text.value += line + "\n"
                                        reprocess_text.update()
                        except Exception as exc:  # noqa: BLE001
                            reprocess_text.value += f"error: {exc}\n"
                            reprocess_text.update()
                            ui.notify(f"Reprocess failed: {exc}", type="negative", position="top")
                        finally:
                            if reprocess_timer["start"] is not None:
                                elapsed = int(time.time() - reprocess_timer["start"])
                                reprocess_timer_label.set_text(f"Elapsed: {elapsed}s")
                            reprocess_timer["running"] = False
                            reprocess_btn.enable()

                # Tool: PSL Enrichment (single production)
                with ui.column().classes("w-full gap-2 mt-4"):
                    psl_btn = ui.button(
                        "Fill Missing Details (Use Google)",
                        icon="playlist_add_check",
                        on_click=lambda e: asyncio.create_task(run_psl_enrich()),
                    ).classes("bg-amber-600 text-white hover:bg-amber-700 px-3 py-1")
                    ui.label(
                        "Fills missing PSL details using Google and links to Locations Master."
                    ).classes("text-sm text-slate-500")
                    psl_timer = {"start": None, "running": False}
                    psl_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

                    psl_output = (
                        ui.expansion("Output", icon="terminal", value=False)
                        .classes("w-full")
                        .props('header-class="q-py-xs" content-class="q-pt-none q-pb-none"')
                    )
                    with psl_output:
                        psl_text = ui.textarea(
                            value="PSL enrichment output will stream here.",
                            placeholder="Streaming progress...",
                        ).classes("w-full text-sm h-36")
                        psl_text.props("readonly")

                    def _update_psl_timer() -> None:
                        if not psl_timer["running"] or psl_timer["start"] is None:
                            return
                        elapsed = int(time.time() - psl_timer["start"])
                        psl_timer_label.set_text(f"Elapsed: {elapsed}s")

                    ui.timer(1.0, _update_psl_timer, active=True)

                    async def run_psl_enrich() -> None:
                        if not locations_db_id:
                            psl_text.value = "error: No production locations table found.\n"
                            psl_text.update()
                            return
                        psl_text.value = "Starting PSL enrichment...\n"
                        psl_text.update()
                        psl_output.value = True
                        psl_output.update()
                        psl_btn.disable()
                        psl_timer["start"] = time.time()
                        psl_timer["running"] = True
                        psl_timer_label.set_text("Elapsed: 0s")
                        try:
                            url = api_url("/api/psl/enrich_stream")
                            params = {"db_id": locations_db_id, "production": production_name}
                            async with httpx.AsyncClient(timeout=None) as client:
                                async with client.stream("GET", url, params=params) as response:
                                    response.raise_for_status()
                                    async for line in response.aiter_lines():
                                        if line is None:
                                            continue
                                        psl_text.value += line + "\n"
                                        psl_text.update()
                        except Exception as exc:  # noqa: BLE001
                            psl_text.value += f"error: {exc}\n"
                            psl_text.update()
                            ui.notify(f"PSL enrichment failed: {exc}", type="negative", position="top")
                        finally:
                            if psl_timer["start"] is not None:
                                elapsed = int(time.time() - psl_timer["start"])
                                psl_timer_label.set_text(f"Elapsed: {elapsed}s")
                            psl_timer["running"] = False
                            psl_btn.enable()
        meta_block.clear()
        with meta_block:
            _render_kv("Notion URL", production.get("url") or "")
            _render_kv("Created", production.get("CreatedTime") or "")
            _render_kv("Last Edited", production.get("LastEditedTime") or "")

    ui.timer(0.1, lambda: asyncio.create_task(load_detail()), once=True)
