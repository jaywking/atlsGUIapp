from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui import assets_list
from app.ui.asset_diagnostics import compute_hero_conflicts
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

    summary_block = ui.expansion("Production Summary", icon="summarize", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    locations_block = ui.expansion("Locations", icon="place", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    assets_block = ui.expansion("Assets", icon="inventory_2", value=True).classes("w-full").props(
        'header-class="bg-slate-50" content-class="q-pt-none q-pb-none"'
    )
    notes_block = ui.expansion("Notes", icon="notes", value=True).classes("w-full").props(
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
        production_name = context.get("production_name") or production.get("Name") or production_id

        title_label.set_text(production.get("Name") or production_id)
        subtitle_label.set_text("")

        summary_block.clear()
        with summary_block:
            _render_kv("Name", production.get("Name") or production_name or "")
            _render_kv("Code", production.get("Abbreviation") or "")
            _render_kv("Status", production.get("Status") or "")

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
                    {"name": "view_psl", "label": "View Details", "field": "master_id", "sortable": False},
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
                            Details
                          </a>
                          <span v-else>--</span>
                        </q-td>
                        """,
                    )

        assets_block.clear()
        with assets_block:
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    response = await client.get(api_url("/api/assets/list"))
                response.raise_for_status()
                payload = response.json() or {}
                if payload.get("status") != "success":
                    raise ValueError(payload.get("message") or "Unable to load assets")
                assets = (payload.get("data") or {}).get("items") or []
            except Exception as exc:  # noqa: BLE001
                ui.label(f"Unable to load assets: {exc}").classes("text-sm text-slate-500")
                assets = []

            production_assets = [
                asset for asset in assets if production_id in (asset.get("production_names") or [])
            ]

            if not production_assets:
                ui.label("No assets linked to this Production.").classes("text-sm text-slate-500")
            else:
                hero_conflicts = compute_hero_conflicts(assets)
                rows, _ = assets_list.build_asset_rows(production_assets, hero_conflicts=hero_conflicts)
                with ui.element("div").classes("w-full overflow-x-auto py-2"):
                    assets_list.build_asset_table(rows, show_actions=True, show_edit_action=False)

        notes_block.clear()
        with notes_block:
            notes = production.get("Notes") or ""
            if notes:
                ui.label(notes).classes("text-sm text-slate-900 dark:text-slate-200")
            else:
                ui.label("No notes.").classes("text-sm text-slate-500")

    ui.timer(0.1, lambda: asyncio.create_task(load_detail()), once=True)
