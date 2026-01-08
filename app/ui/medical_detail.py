from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from nicegui import ui

from app.ui.layout import PAGE_HEADER_CLASSES
from app.ui.medical_shared import (
    build_facility_associations,
    load_locations_master_map,
    load_medical_facilities,
    load_production_location_map,
)


def _render_kv(label: str, value: str) -> None:
    with ui.row().classes("w-full items-start gap-2"):
        ui.label(label).classes("text-sm text-slate-500 w-48 shrink-0")
        ui.label(value or "--").classes("text-sm text-slate-900")


def page_content(medical_facility_id: str) -> None:
    state: Dict[str, Any] = {"facility": None}

    title_label = ui.label("Medical Resource Details").classes("text-xl font-semibold")
    subtitle_label = ui.label(medical_facility_id).classes("text-sm text-slate-500")

    with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px] items-center justify-between"):
        with ui.column().classes("w-full"):
            title_label
            subtitle_label

    with ui.row().classes("items-center gap-2"):
        loading_spinner = ui.spinner(size="md").props("color=primary")
        status_label = ui.label("Loading medical resource...").classes("text-sm text-slate-500")

    summary_block = ui.expansion("Facility Summary", icon="local_hospital", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    productions_block = ui.expansion("Associated Productions", icon="movie", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    locations_block = ui.expansion("Associated Locations", icon="place", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    contact_block = ui.expansion("Contact Information", icon="call", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    notes_block = ui.expansion("Notes", icon="notes", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )

    async def load_detail() -> None:
        facilities, location_map, production_map = await asyncio.gather(
            load_medical_facilities(),
            load_locations_master_map(),
            load_production_location_map(),
        )
        facility = next(
            (item for item in facilities if (item.get("medical_facility_id") or "") == medical_facility_id),
            None,
        )
        if not facility:
            loading_spinner.set_visibility(False)
            status_label.set_text("Medical resource not found.")
            return

        state["facility"] = facility
        production_list, location_list = build_facility_associations(
            facility,
            location_map,
            production_map,
        )

        loading_spinner.set_visibility(False)
        status_label.set_text("")
        title_label.set_text(facility.get("name") or medical_facility_id)
        subtitle_label.set_text(facility.get("medical_facility_id") or medical_facility_id)

        summary_block.clear()
        with summary_block:
            _render_kv("Facility ID", facility.get("medical_facility_id") or "")
            _render_kv("Facility Name", facility.get("name") or "")
            _render_kv("Facility Type", facility.get("facility_type") or "")

        productions_block.clear()
        with productions_block:
            if not production_list:
                ui.label("No associated productions.").classes("text-sm text-slate-500")
            else:
                with ui.column().classes("gap-1"):
                    for production in production_list:
                        prod_id = production.get("id") or ""
                        prod_name = production.get("name") or prod_id
                        if prod_id:
                            ui.link(prod_name, f"/productions/{prod_id}").classes(
                                "text-sm text-slate-900 hover:underline"
                            )
                        else:
                            ui.label(prod_name).classes("text-sm text-slate-900")

        locations_block.clear()
        with locations_block:
            if not location_list:
                ui.label("No associated locations.").classes("text-sm text-slate-500")
            else:
                with ui.column().classes("gap-1"):
                    for loc in location_list:
                        master_id = loc.get("master_id") or ""
                        name = loc.get("name") or master_id
                        if master_id:
                            ui.link(f"{master_id} - {name}".strip(), f"/locations/{master_id}").classes(
                                "text-sm text-slate-900 hover:underline"
                            )
                        else:
                            ui.label(name).classes("text-sm text-slate-900")

        contact_block.clear()
        with contact_block:
            _render_kv("Address", facility.get("address") or "")
            _render_kv("Phone", facility.get("phone") or "")

        notes_block.clear()
        with notes_block:
            notes = facility.get("notes") or ""
            if notes:
                ui.label(notes).classes("text-sm text-slate-900")
            else:
                ui.label("No notes.").classes("text-sm text-slate-500")

    ui.timer(0.1, lambda: asyncio.create_task(load_detail()), once=True)
