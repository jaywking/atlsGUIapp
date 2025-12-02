from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import time

import fastapi
import httpx
import nicegui
import uvicorn
from fastapi import Request
from nicegui import ui

from app.core.settings import settings
from app.ui.layout import PAGE_HEADER_CLASSES


async def _request_json(
    method: str,
    url: str,
    request: Request,
    *,
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = 8.0,
) -> Tuple[bool, Any]:
    try:
        async with httpx.AsyncClient(base_url=str(request.base_url), timeout=timeout) as client:
            response = await client.request(method, url, json=payload)
        response.raise_for_status()
        return True, response.json()
    except Exception as exc:  # noqa: BLE001
        return False, {"error": str(exc)}


def page_content(request: Request) -> None:
    if not settings.DEBUG_ADMIN:
        ui.label("Not authorized.")
        return

    # Heartbeat to keep websocket active during long admin actions
    heartbeat = ui.label("").classes("hidden")
    ui.timer(5.0, lambda: heartbeat.set_text(str(time.time())), active=True)

    state: Dict[str, Any] = {
        "match_all_result": None,
        "cache_status": "Ready.",
        "dedup_count": None,
        "productions": [],
        "productions_loaded": False,
        "diag_result": None,
    }

    run_task = getattr(ui, "run_task", None)

    def start_task(coro):
        if run_task:
            return run_task(coro)
        return asyncio.create_task(coro)

    def format_json(data: Any, *, empty_message: str = "Result will appear after running this action.") -> str:
        if data in (None, "", {}):
            return empty_message
        try:
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            return str(data)

    with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px] items-center justify-between"):
        ui.label("Admin Tools").classes("text-xl font-semibold")
        ui.label("DEBUG_ADMIN enabled").classes("text-sm text-slate-500")

    with ui.column().classes("w-full max-w-4xl gap-3 items-stretch"):
        # Section 1 - Match All Locations
        with ui.expansion("Match All Locations", icon="bolt", value=True).classes("border border-slate-200 dark:border-slate-700"):
            result_code = ui.code(
                format_json(state["match_all_result"], empty_message="Result will appear after running Match All.")
            ).classes("w-full text-sm")

            async def run_match_all() -> None:
                result_code.content = "Running match_all..."
                result_code.update()
                ok, payload = await _request_json("post", "/api/locations/match_all", request)
                if not ok:
                    ui.notify(f"Match All failed: {payload.get('error')}", type="negative", position="top")
                state["match_all_result"] = payload
                result_code.content = format_json(payload)
                result_code.update()

            ui.button(
                "Run Match All",
                icon="play_arrow",
                on_click=lambda e: start_task(run_match_all()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1")

        # Section 2 - Schema Update (placeholder)
        with ui.expansion("Schema Update", icon="schema").classes("border border-slate-200 dark:border-slate-700"):
            ui.button("Run Schema Update", icon="playlist_add").on(
                "click", lambda e: ui.notify("Schema update coming soon.", type="info", position="top")
            )
            ui.button("Preview Schema Changes", icon="preview").on(
                "click", lambda e: ui.notify("Schema preview coming soon.", type="info", position="top")
            )
            ui.label("Coming soon").classes("text-sm text-slate-500")

        # Section 3 - Cache Management
        with ui.expansion("Cache Management", icon="cached").classes("border border-slate-200 dark:border-slate-700"):
            cache_status = ui.label(state["cache_status"]).classes("text-sm text-slate-500")

            async def refresh_cache() -> None:
                cache_status.set_text("Refreshing cache...")
                ok, payload = await _request_json("get", "/system/cache/refresh", request)
                if not ok:
                    ui.notify(f"Cache refresh failed: {payload.get('error')}", type="negative", position="top")
                cache_status.set_text(format_json(payload))

            ui.button(
                "Refresh Cache",
                icon="refresh",
                on_click=lambda e: start_task(refresh_cache()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mb-1")

            ui.button(
                "Purge Dedup Cache",
                icon="delete_sweep",
                on_click=lambda e: ui.notify("Purge Dedup Cache coming soon.", type="info", position="top"),
            ).classes("bg-amber-600 text-white hover:bg-amber-700 px-3 py-1 mb-1")

            ui.button(
                "Reload All Places Data",
                icon="cloud_sync",
                on_click=lambda e: ui.notify("Reload All Places Data coming soon.", type="info", position="top"),
            ).classes("bg-amber-600 text-white hover:bg-amber-700 px-3 py-1")

        # Section 4 - Address Normalization
        with ui.expansion("Address Normalization", icon="home_pin").classes("border border-slate-200 dark:border-slate-700"):
            table_select = ui.select(
                [
                    "AMCL_Locations",
                    "TGD_Locations",
                    "YDEO_Locations",
                    "IPR_Locations",
                    "Locations Master",
                    "Medical Facilities",
                ],
                value="Locations Master",
                label="Select Table",
            ).classes("w-full")

            result_box = ui.code("Run Preview or Apply to see results.", language="json").classes("w-full min-h-[120px]")
            with ui.row().classes("items-center gap-3 mt-2"):
                spinner = ui.spinner(size='lg')
                spinner.visible = False
                elapsed_label = ui.label("").classes("text-sm text-slate-500")
            elapsed_counter = {"value": 0}

            def _tick_elapsed() -> None:
                elapsed_label.text = f"Elapsed: {elapsed_counter['value']}s"
                elapsed_label.update()
                elapsed_counter["value"] = elapsed_counter["value"] + 1

            elapsed_timer = ui.timer(1.0, _tick_elapsed, active=False)

            def _show_result(payload: Any) -> None:
                if payload in (None, "", {}):
                    result_box.content = "No data returned."
                else:
                    try:
                        result_box.content = json.dumps(payload, indent=2, ensure_ascii=False)
                    except Exception:
                        result_box.content = str(payload)
                result_box.update()

            async def do_preview() -> None:
                spinner.visible = True
                result_box.content = "Working..."
                result_box.update()
                elapsed_counter["value"] = 0
                elapsed_label.text = "Elapsed: 0s"
                elapsed_label.update()
                elapsed_timer.active = True

                try:
                    async with httpx.AsyncClient(base_url=str(request.base_url), timeout=30.0) as client:
                        resp = await client.post(
                            "/api/locations/normalize/preview",
                            json={"table": table_select.value}
                        )
                    _show_result(resp.json())
                except Exception as e:  # noqa: BLE001
                    _show_result(f"Error: {e}")
                finally:
                    spinner.visible = False
                    elapsed_timer.active = False

            async def do_apply() -> None:
                spinner.visible = True
                result_box.content = "Applying..."
                result_box.update()
                elapsed_counter["value"] = 0
                elapsed_label.text = "Elapsed: 0s"
                elapsed_label.update()
                elapsed_timer.active = True

                try:
                    async with httpx.AsyncClient(base_url=str(request.base_url), timeout=60.0) as client:
                        resp = await client.post(
                            "/api/locations/normalize/apply",
                            json={"table": table_select.value}
                        )
                    _show_result(resp.json())
                except Exception as e:  # noqa: BLE001
                    _show_result(f"Error: {e}")
                finally:
                    spinner.visible = False
                    elapsed_timer.active = False

            preview_button = ui.button("Preview Normalization", on_click=do_preview).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mb-1")
            apply_button = ui.button("Apply Normalization", on_click=do_apply).classes("mt-2 bg-amber-600 text-white hover:bg-amber-700 px-3 py-1 mb-1")

            preview_button.disable()
            preview_button.bind_visibility_from(spinner, "visible", backward=lambda v: not v)
            preview_button.bind_enabled_from(spinner, "visible", backward=lambda v: not v)

            apply_button.disable()
            apply_button.bind_visibility_from(spinner, "visible", backward=lambda v: not v)
            apply_button.bind_enabled_from(spinner, "visible", backward=lambda v: not v)

        # Section 5 - Reprocess Production Locations
        with ui.expansion("Reprocess Production Locations", icon="refresh").classes(
            "border border-slate-200 dark:border-slate-700"
        ):
            production_select = ui.select(
                options=[],
                label="Select Production",
                value=None,
            ).classes("w-full")
            load_status = ui.label("Loading productions...").classes("text-sm text-slate-500")

            async def load_productions() -> None:
                load_status.set_text("Loading productions...")
                ok, payload = await _request_json("get", "/api/productions/fetch", request)
                if not ok:
                    load_status.set_text(f"Failed to load productions: {payload.get('error')}")
                    ui.notify(f"Failed to load productions: {payload.get('error')}", type="negative", position="top")
                    return
                productions = payload.get("data") or []
                options = []
                for prod in productions:
                    pid = prod.get("ProductionID") or prod.get("id")
                    name = prod.get("Name") or prod.get("name") or pid
                    if pid:
                        options.append({"value": pid, "label": f"{name} ({pid})"})
                production_select.options = options
                state["productions"] = options
                state["productions_loaded"] = True
                if options:
                    production_select.value = options[0]["value"]
                    load_status.set_text(f"Loaded {len(options)} productions.")
                else:
                    load_status.set_text("No productions found.")

            async def reprocess_placeholder() -> None:
                selected = production_select.value
                if not selected:
                    ui.notify("Select a production first.", type="warning", position="top")
                    return
                ui.notify(f"Reprocess for {selected} coming soon.", type="info", position="top")

            ui.button(
                "Reprocess Table",
                icon="table_view",
                on_click=lambda e: start_task(reprocess_placeholder()),
            ).classes("bg-amber-600 text-white hover:bg-amber-700 px-3 py-1 mt-2")

        # Section 6 - Dedup Simple Admin
        with ui.expansion("Dedup Simple Admin", icon="tune").classes("border border-slate-200 dark:border-slate-700"):
            dedup_status = ui.label("Loading duplicate groups...").classes("text-sm text-slate-500")
            ui.label("Deduplication admin tools will be migrated here.").classes("text-sm text-slate-500")

            async def load_dedup_groups() -> None:
                dedup_status.set_text("Loading duplicate groups...")
                ok, payload = await _request_json("get", "/api/locations/master/dedup?refresh=true", request)
                if not ok:
                    dedup_status.set_text(f"Failed to load groups: {payload.get('error')}")
                    ui.notify(f"Failed to load dedup groups: {payload.get('error')}", type="negative", position="top")
                    return
                groups: List[Dict[str, Any]]
                if isinstance(payload, dict):
                    groups = payload.get("duplicate_groups") or []
                elif isinstance(payload, list):
                    groups = payload
                else:
                    groups = []
                state["dedup_count"] = len(groups)
                dedup_status.set_text(f"Loaded {len(groups)} duplicate groups.")

            ui.button(
                "Refresh Duplicate Groups",
                icon="refresh",
                on_click=lambda e: start_task(load_dedup_groups()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mt-2")

        # Section 7 - Diagnostics
        with ui.expansion("Diagnostics", icon="bug_report").classes("border border-slate-200 dark:border-slate-700"):
            diag_code = ui.code(
                format_json(state["diag_result"], empty_message="Run Diagnostics to see results.")
            ).classes("w-full text-sm")

            async def run_diagnostics() -> None:
                diag_code.content = "Running diagnostics..."
                diag_code.update()
                ok, payload = await _request_json("get", "/system/diag", request)
                if not ok:
                    ui.notify(f"Diagnostics failed: {payload.get('error')}", type="negative", position="top")
                state["diag_result"] = payload
                diag_code.content = format_json(payload)
                diag_code.update()

            ui.button(
                "Run Diagnostics",
                icon="bug_report",
                on_click=lambda e: start_task(run_diagnostics()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1")

        # Section 8 - System Info
        with ui.expansion("System Info", icon="info").classes("border border-slate-200 dark:border-slate-700"):
            python_version = sys.version.split()[0]
            uvicorn_version = uvicorn.__version__
            fastapi_version = fastapi.__version__
            nicegui_version = nicegui.__version__

            env_keys = [
                "DEBUG_ADMIN",
                "NOTION_TOKEN",
                "NOTION_LOCATIONS_DB_ID",
                "NOTION_PRODUCTIONS_DB_ID",
                "GOOGLE_MAPS_API_KEY",
                "PRODUCTIONS_CACHE_PATH",
                "LOG_PATH",
                "PRODUCTIONS_SYNC_INTERVAL",
            ]
            env_summary = {key: ("set" if os.getenv(key) else "not set") for key in env_keys}

            ui.label(f"Python version: {python_version}")
            ui.label(f"Uvicorn version: {uvicorn_version}")
            ui.label(f"FastAPI version: {fastapi_version}")
            ui.label(f"NiceGUI version: {nicegui_version}")
            ui.label(f"DEBUG_ADMIN: {settings.DEBUG_ADMIN}")
            ui.label("Environment variables (presence only):").classes("mt-2 text-sm font-semibold")
            ui.code(format_json(env_summary)).classes("w-full text-sm")

    start_task(load_productions())
    start_task(load_dedup_groups())
