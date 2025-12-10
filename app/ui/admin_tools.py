from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

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
        with ui.expansion("Match All Locations", icon="bolt", value=True).classes(
            "border border-slate-200 dark:border-slate-700"
        ):
            progress_box = ui.textarea(
                value="Result will appear after running Match All.",
                placeholder="Progress will stream here...",
            ).classes("w-full text-sm h-48")
            progress_box.props("readonly")

            async def run_match_all_stream() -> None:
                progress_box.value = "Starting...\n"
                progress_box.update()
                btn.disable()
                try:
                    async with httpx.AsyncClient(base_url=str(request.base_url), timeout=None) as client:
                        async with client.stream("GET", "/api/locations/match_all_stream") as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if line is None:
                                    continue
                                progress_box.value += line + "\n"
                                progress_box.update()
                except Exception as exc:  # noqa: BLE001
                    progress_box.value += f"error: {exc}\n"
                    progress_box.update()
                    ui.notify(f"Match All failed: {exc}", type="negative", position="top")
                finally:
                    btn.enable()

            btn = ui.button(
                "Run Match All",
                icon="play_arrow",
                on_click=lambda e: start_task(run_match_all_stream()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1")

        # Section 2 - Schema Update (placeholder)
        with ui.expansion("Schema Update", icon="schema").classes("border border-slate-200 dark:border-slate-700"):
            schema_output = ui.textarea(
                value="Result will appear after running Schema Update.",
                placeholder="Schema update progress will stream here...",
            ).classes("w-full text-sm h-48")
            schema_output.props("readonly")

            async def run_schema_stream() -> None:
                schema_output.value = "Starting schema update...\n"
                schema_output.update()
                schema_btn.disable()
                try:
                    async with httpx.AsyncClient(base_url=str(request.base_url), timeout=None) as client:
                        async with client.stream("GET", "/api/locations/schema_update_stream") as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if line is None:
                                    continue
                                schema_output.value += line + "\n"
                                schema_output.update()
                except Exception as exc:  # noqa: BLE001
                    schema_output.value += f"error: {exc}\n"
                    schema_output.update()
                    ui.notify(f"Schema update failed: {exc}", type="negative", position="top")
                finally:
                    schema_btn.enable()

            schema_btn = ui.button(
                "Run Schema Update",
                icon="playlist_add",
                on_click=lambda e: start_task(run_schema_stream()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mb-1")

        # Section 3 - Cache Management
        with ui.expansion("Cache Management", icon="cached").classes("border border-slate-200 dark:border-slate-700"):
            cache_output = ui.textarea(
                value="Cache progress will appear here.",
                placeholder="Cache management progress will stream here...",
            ).classes("w-full text-sm h-40")
            cache_output.props("readonly")

            async def stream_cache(endpoint: str, btn_ref) -> None:
                cache_output.value = "Starting...\n"
                cache_output.update()
                btn_ref.disable()
                try:
                    async with httpx.AsyncClient(base_url=str(request.base_url), timeout=None) as client:
                        async with client.stream("GET", endpoint) as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if line is None:
                                    continue
                                cache_output.value += line
                                if not line.endswith("\n"):
                                    cache_output.value += "\n"
                                cache_output.update()
                except Exception as exc:  # noqa: BLE001
                    cache_output.value += f"error: {exc}\n"
                    cache_output.update()
                    ui.notify(f"Cache action failed: {exc}", type="negative", position="top")
                finally:
                    btn_ref.enable()

            btn_refresh = ui.button(
                "Refresh Cache",
                icon="refresh",
                on_click=lambda e: start_task(stream_cache("/api/locations/cache_refresh_stream", btn_refresh)),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mb-1")

            btn_purge = ui.button(
                "Purge Dedup Cache",
                icon="delete_sweep",
                on_click=lambda e: start_task(stream_cache("/api/locations/cache_purge_stream", btn_purge)),
            ).classes("bg-amber-600 text-white hover:bg-amber-700 px-3 py-1 mb-1")

            btn_reload = ui.button(
                "Reload All Places Data",
                icon="cloud_sync",
                on_click=lambda e: start_task(stream_cache("/api/locations/cache_reload_stream", btn_reload)),
            ).classes("bg-amber-600 text-white hover:bg-amber-700 px-3 py-1")

        # Section 4 - Address Normalization (Retired)
        with ui.expansion("Address Normalization", icon="home_pin").classes(
            "border border-slate-200 dark:border-slate-700"
        ):
            ui.label(
                "Address normalization is no longer available in the UI. "
                "All new data is normalized at ingest. To repair existing Notion data, use:"
            ).classes("text-sm text-slate-500")
            ui.code("python -m scripts.repair_addresses").classes("w-full text-xs")

        # Section 5 - Reprocess Production Locations
        with ui.expansion("Reprocess Production Locations", icon="refresh").classes(
            "border border-slate-200 dark:border-slate-700"
        ):
            production_select = ui.select(
                options={},
                label="Select Production",
                value=None,
            ).classes("w-full")
            load_status = ui.label("Loading productions...").classes("text-sm text-slate-500")
            reprocess_output = ui.textarea(
                value="Reprocess output will appear here.",
                placeholder="Streaming progress...",
            ).classes("w-full text-sm h-48")
            reprocess_output.props("readonly")

            async def load_productions() -> None:
                load_status.set_text("Loading productions...")
                ok, payload = await _request_json("get", "/api/locations/production_dbs", request)
                if not ok:
                    load_status.set_text(f"Failed to load productions: {payload.get('error')}")
                    ui.notify(f"Failed to load productions: {payload.get('error')}", type="negative", position="top")
                    return
                productions = payload.get("data") or []
                options_list = []
                for prod in productions:
                    db_id = prod.get("locations_db_id") or ""
                    if not db_id:
                        continue
                    label = prod.get("display_name") or prod.get("production_title") or "Production"
                    pid = prod.get("production_id")
                    if pid and label and label != pid:
                        label = f"{label} ({pid})"
                    options_list.append({"label": label, "value": db_id})
                production_select.options = options_list  # list of {label, value}
                state["productions"] = options_list
                state["productions_loaded"] = True
                if options_list:
                    production_select.value = options_list[0]["value"]
                    load_status.set_text(f"Loaded {len(options_list)} productions.")
                else:
                    load_status.set_text("No productions found.")

            async def run_reprocess_stream() -> None:
                selected = production_select.value
                if not selected:
                    ui.notify("Select a production first.", type="warning", position="top")
                    return
                selected_label = next((k for k, v in (production_select.options or {}).items() if v == selected), selected)
                reprocess_output.value = f"Starting reprocess for {selected_label} ({selected})...\n"
                reprocess_output.update()
                reprocess_btn.disable()
                try:
                    async with httpx.AsyncClient(base_url=str(request.base_url), timeout=None) as client:
                        async with client.stream("GET", f"/api/locations/reprocess_stream?db_id={selected}") as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if line is None:
                                    continue
                                reprocess_output.value += line
                                if not line.endswith("\n"):
                                    reprocess_output.value += "\n"
                                reprocess_output.update()
                except Exception as exc:  # noqa: BLE001
                    reprocess_output.value += f"error: {exc}\n"
                    reprocess_output.update()
                    ui.notify(f"Reprocess failed: {exc}", type="negative", position="top")
                finally:
                    reprocess_btn.enable()

            reprocess_btn = ui.button(
                "Reprocess Table",
                icon="table_view",
                on_click=lambda e: start_task(run_reprocess_stream()),
            ).classes("bg-amber-600 text-white hover:bg-amber-700 px-3 py-1 mt-2")

        # Section 6 - Dedup Simple Admin
        with ui.expansion("Dedup Simple Admin", icon="tune").classes("border border-slate-200 dark:border-slate-700"):
            dedup_output = ui.textarea(
                value="Dedup results will stream here.",
                placeholder="Streaming dedup scan...",
            ).classes("w-full text-sm h-40")
            dedup_output.props("readonly")

            async def run_dedup_stream() -> None:
                dedup_output.value = "Starting dedup scan...\n"
                dedup_output.update()
                dedup_btn.disable()
                try:
                    async with httpx.AsyncClient(base_url=str(request.base_url), timeout=None) as client:
                        async with client.stream("GET", "/api/locations/dedup_stream") as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if line is None:
                                    continue
                                dedup_output.value += line
                                if not line.endswith("\n"):
                                    dedup_output.value += "\n"
                                dedup_output.update()
                except Exception as exc:  # noqa: BLE001
                    dedup_output.value += f"error: {exc}\n"
                    dedup_output.update()
                finally:
                    dedup_btn.enable()

            dedup_btn = ui.button(
                "Run Dedup Scan",
                icon="refresh",
                on_click=lambda e: start_task(run_dedup_stream()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mt-2")

        # Section 7 - Diagnostics (streaming)
        with ui.expansion("Diagnostics", icon="bug_report").classes("border border-slate-200 dark:border-slate-700"):
            diag_output = ui.textarea(
                value="Diagnostics output will stream here.",
                placeholder="Streaming diagnostics...",
            ).classes("w-full text-sm h-40")
            diag_output.props("readonly")

            async def run_diagnostics() -> None:
                diag_output.value = "Starting diagnostics...\n"
                diag_output.update()
                diag_btn.disable()
                try:
                    async with httpx.AsyncClient(base_url=str(request.base_url), timeout=None) as client:
                        async with client.stream("GET", "/api/locations/diagnostics_stream") as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if line is None:
                                    continue
                                diag_output.value += line
                                if not line.endswith("\n"):
                                    diag_output.value += "\n"
                                diag_output.update()
                except Exception as exc:  # noqa: BLE001
                    diag_output.value += f"error: {exc}\n"
                    diag_output.update()
                    ui.notify(f"Diagnostics failed: {exc}", type="negative", position="top")
                finally:
                    diag_btn.enable()

            diag_btn = ui.button(
                "Run Diagnostics",
                icon="bug_report",
                on_click=lambda e: start_task(run_diagnostics()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1")

        # Section 8 - System Info
        with ui.expansion("System Info", icon="info").classes("border border-slate-200 dark:border-slate-700"):
            sys_output = ui.code("System info will appear here.").classes("w-full text-sm")

            async def load_system_info() -> None:
                sys_output.content = "Loading system info..."
                sys_output.update()
                ok, payload = await _request_json("get", "/api/locations/system_info", request)
                if not ok:
                    sys_output.content = f"error: {payload.get('error')}"
                    sys_output.update()
                    return
                sys_output.content = format_json(payload)
                sys_output.update()

            ui.button(
                "Load System Info",
                icon="info",
                on_click=lambda e: start_task(load_system_info()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mt-2")

    start_task(load_productions())
