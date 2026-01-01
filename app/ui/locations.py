from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx
from nicegui import ui

from app.services.api_client import api_url


def page_content() -> None:
    """Locations Master search page (read-only)."""

    state: Dict[str, Any] = {"rows": [], "searched": False}

    with ui.column().classes("w-full gap-3"):
        with ui.row().classes("items-end gap-2 flex-wrap w-full"):
            production_input = ui.input(label="Production Name").props("dense clearable").classes("flex-1 min-w-[220px]")
            name_input = ui.input(label="Practical Name / Name").props("dense clearable").classes("flex-1 min-w-[220px]")
            city_input = ui.input(label="City").props("dense clearable").classes("w-48")
            state_input = ui.input(label="State").props("dense clearable").classes("w-24")
            search_button = ui.button("Search", icon="search").classes(
                "bg-blue-500 text-white hover:bg-slate-100 dark:hover:bg-slate-800"
            )
            clear_button = ui.button("Clear", icon="refresh").classes(
                "bg-slate-200 text-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800"
            )
            spinner = ui.spinner(size="md").props("color=primary").style("display: none;")

        with ui.expansion("Advanced Filters", icon="tune", value=False).classes("w-full"):
            with ui.column().classes("w-full gap-2"):
                with ui.row().classes("items-end gap-2 flex-wrap w-full"):
                    full_address_input = ui.input(label="Full Address").props("dense clearable").classes("w-80")
                    zip_input = ui.input(label="Zip").props("dense clearable").classes("w-24")
                    country_input = ui.input(label="Country").props("dense clearable").classes("w-24")
                    country_input.value = "US"
                    county_input = ui.input(label="County").props("dense clearable").classes("w-40")
                    borough_input = ui.input(label="Borough").props("dense clearable").classes("w-40")
                with ui.row().classes("items-end gap-2 flex-wrap w-full"):
                    types_input = ui.select(
                        [],
                        label="Place Types",
                        multiple=True,
                    ).props("use-input fill-input clearable new-value-mode=add-unique").classes("w-80")
                    op_status_input = ui.select(
                        ["OPERATIONAL", "CLOSED_TEMPORARILY", "CLOSED_PERMANENTLY"],
                        label="Location Op Status",
                        value=None,
                    ).props("clearable").classes("w-48")
                    status_input = ui.select(
                        ["Ready", "Matched", "Unresolved"],
                        label="Status",
                        value=None,
                    ).props("clearable").classes("w-36")
                    place_id_input = ui.input(label="Place ID").props("dense clearable").classes("w-72")
                    master_id_input = ui.input(label="Location Master ID").props("dense clearable").classes("w-40")

        with ui.row().classes("items-center justify-between w-full gap-2"):
            status_label = ui.label("Run a search to see Locations Master results.").classes("text-sm text-slate-500")
            with ui.row().classes("items-center gap-2"):
                prev_button = ui.button("Prev").classes("bg-slate-200 text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800").props("disable")
                next_button = ui.button("Next").classes("bg-slate-200 text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800").props("disable")

    columns = [
        {
            "name": "master_id",
            "label": "Location Master ID",
            "field": "master_id",
            "sortable": True,
            "style": "width: 160px;",
            "headerStyle": "width: 160px;",
        },
        {"name": "name", "label": "Practical Name", "field": "name", "sortable": True},
        {"name": "full_address", "label": "Full Address", "field": "full_address", "sortable": True},
        {"name": "city", "label": "City", "field": "city", "sortable": True},
        {"name": "state", "label": "State", "field": "state", "sortable": True},
        {"name": "place_type", "label": "Place Type", "field": "place_type", "sortable": True},
        {"name": "google_map", "label": "Google Map", "field": "google_maps_url", "sortable": False},
    ]

    table_container = ui.element("div").classes("w-full overflow-x-auto py-2").style("display: none;")
    with table_container:
        table = (
            ui.table(columns=columns, rows=[], row_key="row_id")
            .classes("w-full text-sm q-table--flat")
            .props('flat square wrap-cells sort-by="master_id" separator="horizontal"')
        )

        table.add_slot(
            "body-cell-name",
            """
            <q-td :props="props">
              <span class="font-semibold">{{ props.row.name }}</span>
            </q-td>
            """,
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
            "body-cell-google_map",
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

    def _set_loading(is_loading: bool) -> None:
        spinner.style("display: inline-block;" if is_loading else "display: none;")
        search_button.set_enabled(not is_loading)
        clear_button.set_enabled(not is_loading)

    def _set_results(rows: List[Dict[str, Any]]) -> None:
        table.rows = rows
        table.update()
        table_container.style("display: block;")

    async def run_search() -> None:
        params: Dict[str, Any] = {}
        production_name = (production_input.value or "").strip()
        if production_name:
            params["production_name"] = production_name
        else:
            params = {
                "location_name": (name_input.value or "").strip(),
                "full_address": (full_address_input.value or "").strip(),
                "city": (city_input.value or "").strip(),
                "state": (state_input.value or "").strip(),
                "country": (country_input.value or "").strip(),
                "zip_code": (zip_input.value or "").strip(),
                "county": (county_input.value or "").strip(),
                "borough": (borough_input.value or "").strip(),
                "place_type": ",".join([t.strip() for t in (types_input.value or []) if t.strip()]),
                "status": (status_input.value or "").strip(),
                "location_op_status": (op_status_input.value or "").strip(),
                "place_id": (place_id_input.value or "").strip(),
                "master_id": (master_id_input.value or "").strip(),
            }

        _set_loading(True)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(api_url("/api/locations/search_master"), params=params)
            response.raise_for_status()
            payload = response.json() or {}
            if payload.get("status") != "success":
                raise ValueError(payload.get("message") or "Search failed")
            data = payload.get("data") or {}
            items = data.get("items") or []
            total = data.get("total", len(items))
            truncated = bool(data.get("truncated"))

            rows: List[Dict[str, Any]] = []
            for item in items:
                rows.append(
                    {
                        "row_id": item.get("row_id") or "",
                        "master_id": item.get("master_id") or "",
                        "name": item.get("name") or "",
                        "full_address": item.get("full_address") or "",
                        "city": item.get("city") or "",
                        "state": item.get("state") or "",
                        "place_type": item.get("place_type") or "",
                        "google_maps_url": item.get("google_maps_url") or "",
                    }
                )

            state["rows"] = rows
            state["searched"] = True
            _set_results(rows)
            suffix = f" Showing {len(rows)} of {total}." if truncated else ""
            status_label.set_text(f"Returned {len(rows)} Locations.{suffix}")
        except Exception as exc:  # noqa: BLE001
            status_label.set_text(f"Search failed: {exc}")
            table_container.style("display: none;")
        finally:
            _set_loading(False)

    def clear_search() -> None:
        production_input.set_value("")
        name_input.set_value("")
        city_input.set_value("")
        state_input.set_value("")
        country_input.set_value("US")
        full_address_input.set_value("")
        zip_input.set_value("")
        county_input.set_value("")
        borough_input.set_value("")
        types_input.set_value([])
        op_status_input.set_value(None)
        status_input.set_value(None)
        place_id_input.set_value("")
        master_id_input.set_value("")
        state["rows"] = []
        state["searched"] = False
        table.rows = []
        table.update()
        table_container.style("display: none;")
        status_label.set_text("Run a search to see Locations Master results.")

    search_button.on("click", lambda e=None: asyncio.create_task(run_search()))
    clear_button.on("click", lambda e=None: clear_search())
