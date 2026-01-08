from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui.asset_diagnostics import compute_asset_diagnostics, compute_hero_conflicts, severity_counts
from app.ui.layout import PAGE_HEADER_CLASSES


def _join(values: List[str]) -> str:
    cleaned = [v for v in values if v]
    return ", ".join(cleaned)


def _diag_summary(diags: List[Dict[str, str]]) -> str:
    counts = severity_counts(diags)
    if not counts:
        return ""
    return " ".join([f"{key}:{counts[key]}" for key in ("WARNING", "CHECK", "INFO") if key in counts])


def build_asset_rows(
    items: List[Dict[str, Any]],
    *,
    hero_conflicts: set[str] | None = None,
) -> tuple[List[Dict[str, Any]], int]:
    if hero_conflicts is None:
        hero_conflicts = compute_hero_conflicts(items)
    rows: List[Dict[str, Any]] = []
    diag_assets = 0

    for asset in items:
        diags = compute_asset_diagnostics(asset, hero_conflicts=hero_conflicts)
        counts = severity_counts(diags)
        diag_badges = []
        if "WARNING" in counts:
            diag_badges.append(
                {
                    "key": "WARNING",
                    "label": f"WARNING:{counts['WARNING']}",
                    "classes": "text-xs px-2 py-0.5 rounded border border-rose-200 text-rose-700 bg-rose-50",
                }
            )
        if "CHECK" in counts:
            diag_badges.append(
                {
                    "key": "CHECK",
                    "label": f"CHECK:{counts['CHECK']}",
                    "classes": "text-xs px-2 py-0.5 rounded border border-amber-200 text-amber-700 bg-amber-50",
                }
            )
        if "INFO" in counts:
            diag_badges.append(
                {
                    "key": "INFO",
                    "label": f"INFO:{counts['INFO']}",
                    "classes": "text-xs px-2 py-0.5 rounded border border-slate-200 text-slate-600 bg-slate-50",
                }
            )
        if diags:
            diag_assets += 1
        rows.append(
            {
                "asset_id": asset.get("asset_id") or "",
                "asset_name": asset.get("asset_name") or "",
                "asset_type": asset.get("asset_type") or "",
                "asset_categories": _join(asset.get("asset_categories") or []),
                "productions": _join(asset.get("production_names") or []),
                "locations_master": _join(asset.get("locations_master_names") or []),
                "visibility_flag": asset.get("visibility_flag") or "",
                "diagnostics": _diag_summary(diags),
                "diagnostic_list": diags,
                "diagnostic_counts": diag_badges,
            }
        )
    return rows, diag_assets


def build_asset_table(
    rows: List[Dict[str, Any]],
    *,
    show_actions: bool = True,
    show_edit_action: bool = True,
) -> ui.table:
    columns = [
        {"name": "asset_id", "label": "Asset ID", "field": "asset_id", "sortable": True},
        {"name": "asset_name", "label": "Asset Name", "field": "asset_name", "sortable": True},
        {"name": "asset_type", "label": "Asset Type", "field": "asset_type", "sortable": True},
        {"name": "asset_categories", "label": "Asset Category", "field": "asset_categories", "sortable": False},
        {"name": "productions", "label": "Production(s)", "field": "productions", "sortable": False},
        {"name": "locations_master", "label": "Locations Master", "field": "locations_master", "sortable": False},
        {"name": "visibility_flag", "label": "Visibility Flag", "field": "visibility_flag", "sortable": True},
        {"name": "diagnostics", "label": "Diagnostics", "field": "diagnostics", "sortable": False},
    ]
    if show_actions:
        columns.append({"name": "actions", "label": "Actions", "field": "asset_id", "sortable": False})

    table = (
        ui.table(columns=columns, rows=rows, row_key="asset_id")
        .classes("w-full text-sm q-table--flat min-w-[1300px]")
        .props('flat wrap-cells square separator="horizontal"')
    )

    table.add_slot(
        "body-cell-asset_id",
        """
        <q-td :props="props">
          <a
            v-if="props.row.asset_id"
            :href="`/assets/${props.row.asset_id}`"
            target="_blank"
            class="text-slate-700 hover:text-slate-900 hover:underline whitespace-nowrap"
          >
            {{ props.row.asset_id }}
          </a>
          <span v-else>--</span>
        </q-td>
        """,
    )

    table.add_slot(
        "body-cell-diagnostics",
        """
        <q-td :props="props">
          <div class="flex flex-wrap gap-2">
            <span v-for="item in (props.row.diagnostic_counts || [])" :key="item.key"
              :class="item.classes">
              {{ item.label }}
            </span>
            <span v-if="!props.row.diagnostic_counts || props.row.diagnostic_counts.length === 0">--</span>
          </div>
        </q-td>
        """,
    )

    if show_actions:
        edit_action = ""
        if show_edit_action:
            edit_action = """
            <a
              v-if="props.row.asset_id"
              :href="`/assets/${props.row.asset_id}?edit=1`"
              target="_blank"
              class="text-slate-700 hover:text-slate-900 hover:underline"
            >Edit Asset</a>
            """
        table.add_slot(
            "body-cell-actions",
            f"""
            <q-td :props="props">
              <div class="flex gap-2 items-center">
                <a
                  v-if="props.row.asset_id"
                  :href="`/assets/${{props.row.asset_id}}`"
                  target="_blank"
                  class="text-slate-700 hover:text-slate-900 hover:underline"
                >View Asset</a>
                {edit_action}
              </div>
            </q-td>
            """,
        )

    return table


def page_content() -> None:
    state: Dict[str, Any] = {"rows": [], "filtered": [], "filters": {}, "diag_count": 0}

    with ui.column().classes("w-full gap-2"):
        with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px]"):
            with ui.row().classes("items-center gap-2 flex-wrap w-full"):
                refresh_button = ui.button("Refresh").classes(
                    "bg-blue-500 text-white hover:bg-slate-100 dark:hover:bg-slate-800"
                )
                spinner = ui.spinner(size="md").style("display: none;")
                type_filter = ui.select(["All"], label="Asset Type").props("dense clearable").classes("w-48")
                production_filter = ui.select(["All"], label="Production").props("dense clearable").classes("w-64")
                location_filter = ui.select(["All"], label="Locations Master").props("dense clearable").classes("w-56")
                visibility_filter = ui.select(["All", "Visible", "Hidden", "Hero"], label="Visibility Flag").props(
                    "dense clearable"
                ).classes("w-40")
                diag_filter = ui.select(["All", "Yes", "No"], label="Has Diagnostics").props("dense clearable").classes("w-44")

        diag_summary = ui.label("").classes("text-sm text-slate-500")
        diag_summary.set_visibility(False)

    with ui.element("div").classes("w-full overflow-x-auto py-2"):
        table = build_asset_table([], show_actions=True, show_edit_action=True)

    async def load_assets() -> None:
        spinner.style("display: inline-block;")
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(api_url("/api/assets/list"))
            response.raise_for_status()
            payload = response.json() or {}
            if payload.get("status") != "success":
                raise ValueError(payload.get("message") or "Unable to load assets")
            items = (payload.get("data") or {}).get("items") or []
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Unable to load assets: {exc}", type="warning", position="top")
            spinner.style("display: none;")
            return
        finally:
            spinner.style("display: none;")

        rows, diag_assets = build_asset_rows(items)

        state["rows"] = rows
        state["diag_count"] = diag_assets
        _refresh_filters()
        apply_filters()

    def _refresh_filters() -> None:
        rows = state.get("rows") or []
        type_options = sorted({r.get("asset_type") for r in rows if r.get("asset_type")}) or []
        prod_options = sorted({p for r in rows for p in (r.get("productions") or "").split(", ") if p})
        loc_options = sorted({p for r in rows for p in (r.get("locations_master") or "").split(", ") if p})
        type_filter.options = ["All"] + type_options
        production_filter.options = ["All"] + prod_options
        location_filter.options = ["All"] + loc_options
        for ctl in (type_filter, production_filter, location_filter):
            ctl.update()

    def apply_filters() -> None:
        rows = list(state.get("rows") or [])
        type_value = (type_filter.value or "All").strip()
        production_value = (production_filter.value or "All").strip()
        location_value = (location_filter.value or "All").strip()
        visibility_value = (visibility_filter.value or "All").strip()
        diag_value = (diag_filter.value or "All").strip()

        if type_value != "All":
            rows = [r for r in rows if r.get("asset_type") == type_value]
        if production_value != "All":
            rows = [r for r in rows if production_value in (r.get("productions") or "").split(", ")]
        if location_value != "All":
            rows = [r for r in rows if location_value in (r.get("locations_master") or "").split(", ")]
        if visibility_value != "All":
            rows = [r for r in rows if (r.get("visibility_flag") or "") == visibility_value]
        if diag_value == "Yes":
            rows = [r for r in rows if r.get("diagnostic_list")]
        elif diag_value == "No":
            rows = [r for r in rows if not r.get("diagnostic_list")]

        rows.sort(key=lambda r: ((r.get("asset_type") or "").lower(), (r.get("asset_name") or "").lower()))
        table.rows = rows
        table.update()

        diag_count = sum(1 for r in rows if r.get("diagnostic_list"))
        if diag_count > 1:
            diag_summary.set_text(f"{diag_count} assets have checks.")
            diag_summary.set_visibility(True)
        else:
            diag_summary.set_visibility(False)

    refresh_button.on("click", lambda e: asyncio.create_task(load_assets()))
    type_filter.on_value_change(lambda e: apply_filters())
    production_filter.on_value_change(lambda e: apply_filters())
    location_filter.on_value_change(lambda e: apply_filters())
    visibility_filter.on_value_change(lambda e: apply_filters())
    diag_filter.on_value_change(lambda e: apply_filters())

    ui.timer(0.1, lambda: asyncio.create_task(load_assets()), once=True)
