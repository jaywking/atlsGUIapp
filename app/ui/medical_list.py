from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from nicegui import ui

from app.ui.layout import PAGE_HEADER_CLASSES
from app.ui.medical_shared import (
    build_facility_associations,
    load_locations_master_map,
    load_medical_facilities,
    load_production_location_map,
)

logger = logging.getLogger(__name__)


def _join(values: List[str]) -> str:
    cleaned = [v for v in values if v]
    return ", ".join(cleaned)


def page_content() -> None:
    state: Dict[str, Any] = {
        "rows": [],
    }

    with ui.column().classes("w-full gap-2"):
        with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px]"):
            with ui.row().classes("items-center gap-2 flex-wrap w-full"):
                refresh_button = ui.button("Refresh").classes(
                    "bg-blue-500 text-white hover:bg-slate-100 dark:hover:bg-slate-800"
                )
                spinner = ui.spinner(size="md").style("display: none;")
        status_label = ui.label("Loading medical resources...").classes("text-sm text-slate-500")

    columns = [
        {"name": "facility_name", "label": "Facility Name", "field": "facility_name", "sortable": True},
        {"name": "facility_type", "label": "Type", "field": "facility_type", "sortable": True},
        {"name": "productions", "label": "Associated Production(s)", "field": "productions", "sortable": False},
        {"name": "locations", "label": "Associated Location(s)", "field": "locations", "sortable": False},
        {"name": "phone", "label": "Phone", "field": "phone", "sortable": False},
        {"name": "actions", "label": "Actions", "field": "medical_facility_id", "sortable": False},
    ]

    with ui.element("div").classes("w-full overflow-x-auto py-2"):
        table = (
            ui.table(columns=columns, rows=[], row_key="row_id")
            .classes("w-full text-sm q-table--flat min-w-[1100px]")
            .props('flat wrap-cells square separator="horizontal"')
        )

        with table.add_slot("body-cell-facility_name"):
            ui.html(
                """
                <q-td :props="props">
                  <a
                    v-if="props.row.medical_facility_id"
                    :href="`/medical/${props.row.medical_facility_id}`"
                    target="_blank"
                    class="text-slate-700 hover:text-slate-900 hover:underline"
                  >
                    {{ props.row.facility_name }}
                  </a>
                  <span v-else>{{ props.row.facility_name }}</span>
                </q-td>
                """,
                sanitize=False,
            )

        with table.add_slot("body-cell-actions"):
            ui.html(
                """
                <q-td :props="props">
                  <a
                    v-if="props.row.medical_facility_id"
                    :href="`/medical/${props.row.medical_facility_id}`"
                    target="_blank"
                    class="text-slate-700 hover:text-slate-900 hover:underline"
                  >
                    View Medical Resource
                  </a>
                  <span v-else>--</span>
                </q-td>
                """,
                sanitize=False,
            )

    def set_loading(is_loading: bool) -> None:
        spinner.style("display: inline-block;" if is_loading else "display: none;")
        refresh_button.set_enabled(not is_loading)
        if is_loading:
            status_label.set_text("Loading medical resources...")

    async def load_data() -> None:
        set_loading(True)
        try:
            facilities, location_map, production_map = await asyncio.gather(
                load_medical_facilities(),
                load_locations_master_map(),
                load_production_location_map(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to load medical data: %s", exc)
            status_label.set_text("Unable to load medical resources.")
            set_loading(False)
            return

        rows: List[Dict[str, Any]] = []
        for facility in facilities:
            production_list, location_list = build_facility_associations(
                facility,
                location_map,
                production_map,
            )
            rows.append(
                {
                    "row_id": facility.get("row_id") or facility.get("medical_facility_id") or "",
                    "medical_facility_id": facility.get("medical_facility_id") or "",
                    "facility_name": facility.get("name") or "",
                    "facility_type": facility.get("facility_type") or "",
                    "productions": _join([p.get("name") or "" for p in production_list]) or "--",
                    "locations": _join([l.get("master_id") or "" for l in location_list]) or "--",
                    "phone": facility.get("phone") or "--",
                }
            )

        rows.sort(key=lambda r: (r.get("facility_name") or "").lower())
        table.rows = rows
        table.update()
        status_label.set_text(f"Returned {len(rows)} medical resources.")
        set_loading(False)

    refresh_button.on("click", lambda e: asyncio.create_task(load_data()))
    ui.timer(0.1, lambda: asyncio.create_task(load_data()), once=True)
