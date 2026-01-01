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

    # Expand to full available width (no max width constraint) for better visibility of admin panels.
    with ui.column().classes("w-full max-w-none gap-3 items-stretch").style("width: 100%; max-width: 100%;"):
        # Section 1 - Match All Locations
        with ui.expansion("Match All Locations", icon="bolt", value=False).classes(
            "border border-slate-200 dark:border-slate-700 w-full"
        ):
            ui.label(
                "Matches all Locations Master rows against known places and writes match results to Notion."
            ).classes("text-sm text-slate-500")
            match_timer = {"start": None, "running": False}
            match_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

            progress_box = ui.textarea(
                value="Result will appear after running Match All.",
                placeholder="Progress will stream here...",
            ).classes("w-full text-sm h-48")
            progress_box.props("readonly")

            def _update_match_timer() -> None:
                if not match_timer["running"] or match_timer["start"] is None:
                    return
                elapsed = int(time.time() - match_timer["start"])
                match_timer_label.set_text(f"Elapsed: {elapsed}s")

            ui.timer(1.0, _update_match_timer, active=True)

            async def run_match_all_stream() -> None:
                progress_box.value = "Starting...\n"
                progress_box.update()
                btn.disable()
                match_timer["start"] = time.time()
                match_timer["running"] = True
                match_timer_label.set_text("Elapsed: 0s")
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
                    if match_timer["start"] is not None:
                        elapsed = int(time.time() - match_timer["start"])
                        match_timer_label.set_text(f"Elapsed: {elapsed}s")
                    match_timer["running"] = False
                    btn.enable()

            btn = ui.button(
                "Run Match All",
                icon="play_arrow",
                on_click=lambda e: start_task(run_match_all_stream()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1")

        # Section 2 - Schema Update (placeholder)
        with ui.expansion("Schema Update", icon="schema").classes("border border-slate-200 dark:border-slate-700 w-full"):
            ui.label(
                "Ensures Locations Master and production tables include canonical schema fields."
            ).classes("text-sm text-slate-500")
            schema_timer = {"start": None, "running": False}
            schema_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

            schema_output = ui.textarea(
                value="Result will appear after running Schema Update.",
                placeholder="Schema update progress will stream here...",
            ).classes("w-full text-sm h-48")
            schema_output.props("readonly")

            def _update_schema_timer() -> None:
                if not schema_timer["running"] or schema_timer["start"] is None:
                    return
                elapsed = int(time.time() - schema_timer["start"])
                schema_timer_label.set_text(f"Elapsed: {elapsed}s")

            ui.timer(1.0, _update_schema_timer, active=True)

            async def run_schema_stream() -> None:
                schema_output.value = "Starting schema update...\n"
                schema_output.update()
                schema_btn.disable()
                schema_timer["start"] = time.time()
                schema_timer["running"] = True
                schema_timer_label.set_text("Elapsed: 0s")
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
                    if schema_timer["start"] is not None:
                        elapsed = int(time.time() - schema_timer["start"])
                        schema_timer_label.set_text(f"Elapsed: {elapsed}s")
                    schema_timer["running"] = False
                    schema_btn.enable()

            schema_btn = ui.button(
                "Run Schema Update",
                icon="playlist_add",
                on_click=lambda e: start_task(run_schema_stream()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mb-1")

        # Section 3 - Cache Management
        with ui.expansion("Cache Management", icon="cached").classes("border border-slate-200 dark:border-slate-700 w-full"):
            ui.label(
                "Refreshes or purges cached Notion data used by the app."
            ).classes("text-sm text-slate-500")
            cache_timer = {"start": None, "running": False}
            cache_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

            cache_output = ui.textarea(
                value="Cache progress will appear here.",
                placeholder="Cache management progress will stream here...",
            ).classes("w-full text-sm h-40")
            cache_output.props("readonly")

            def _update_cache_timer() -> None:
                if not cache_timer["running"] or cache_timer["start"] is None:
                    return
                elapsed = int(time.time() - cache_timer["start"])
                cache_timer_label.set_text(f"Elapsed: {elapsed}s")

            ui.timer(1.0, _update_cache_timer, active=True)

            async def stream_cache(endpoint: str, btn_ref) -> None:
                cache_output.value = "Starting...\n"
                cache_output.update()
                btn_ref.disable()
                cache_timer["start"] = time.time()
                cache_timer["running"] = True
                cache_timer_label.set_text("Elapsed: 0s")
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
                    if cache_timer["start"] is not None:
                        elapsed = int(time.time() - cache_timer["start"])
                        cache_timer_label.set_text(f"Elapsed: {elapsed}s")
                    cache_timer["running"] = False
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

        # Section 4 - Schema Report (diagnostic)
        with ui.expansion("Generate Schema Report", icon="description").classes(
            "border border-slate-200 dark:border-slate-700 w-full"
        ):
            ui.label(
                "Generates a read-only report of current Notion schema fields for key tables."
            ).classes("text-sm text-slate-500")
            report_timer = {"start": None, "running": False}
            report_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

            schema_report_output = ui.textarea(
                value="Press the button to generate a Notion schema report.",
                placeholder="Schema report progress will stream here...",
            ).classes("w-full text-sm h-40")
            schema_report_output.props("readonly")

            def _update_report_timer() -> None:
                if not report_timer["running"] or report_timer["start"] is None:
                    return
                elapsed = int(time.time() - report_timer["start"])
                report_timer_label.set_text(f"Elapsed: {elapsed}s")

            ui.timer(1.0, _update_report_timer, active=True)

            async def run_schema_report_stream() -> None:
                schema_report_output.value = "Starting schema report...\n"
                schema_report_output.update()
                schema_report_btn.disable()
                report_timer["start"] = time.time()
                report_timer["running"] = True
                report_timer_label.set_text("Elapsed: 0s")
                try:
                    async with httpx.AsyncClient(base_url=str(request.base_url), timeout=None) as client:
                        async with client.stream("GET", "/api/schema_report/stream") as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if line is None:
                                    continue
                                schema_report_output.value += line
                                if not line.endswith("\n"):
                                    schema_report_output.value += "\n"
                                schema_report_output.update()
                except Exception as exc:  # noqa: BLE001
                    schema_report_output.value += f"error: {exc}\n"
                    schema_report_output.update()
                    ui.notify(f"Schema report failed: {exc}", type="negative", position="top")
                finally:
                    if report_timer["start"] is not None:
                        elapsed = int(time.time() - report_timer["start"])
                        report_timer_label.set_text(f"Elapsed: {elapsed}s")
                    report_timer["running"] = False
                    schema_report_btn.enable()

            schema_report_btn = ui.button(
                "Generate Schema Report",
                icon="description",
                on_click=lambda e: start_task(run_schema_report_stream()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1")

        # Section 6 - PSL Enrichment (Batch Only)
        with ui.expansion("PSL Enrichment (Batch)", icon="map").classes("border border-slate-200 dark:border-slate-700 w-full"):
            ui.label(
                "Batch PSL enrichment is currently disabled. Use the per-production tool instead."
            ).classes("text-sm text-slate-500")

        # Section 7 - PSL Enrichment Debug
        with ui.expansion("PSL Enrichment Debug", icon="bug_report").classes("border border-slate-200 dark:border-slate-700"):
            ui.label(
                "Shows raw payloads and computed options used by PSL enrichment for troubleshooting."
            ).classes("text-sm text-slate-500")
            psl_debug_timer = {"start": None, "running": False}
            psl_debug_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

            psl_debug_counts = ui.label("Load productions to view debug data.").classes("text-sm text-slate-500")
            psl_debug_raw = ui.textarea(
                value="Raw /api/locations/production_dbs payload will appear here.",
                placeholder="Run Load productions first.",
            ).classes("w-full text-xs h-40")
            psl_debug_raw.props("readonly")
            psl_debug_options = ui.textarea(
                value="Computed select options will appear here.",
                placeholder="Run Load productions first.",
            ).classes("w-full text-xs h-40")
            psl_debug_options.props("readonly")
            psl_debug_master = ui.textarea(
                value="Raw /api/productions/fetch payload will appear here.",
                placeholder="Run Load productions first.",
            ).classes("w-full text-xs h-40")
            psl_debug_master.props("readonly")

            async def load_production_debug() -> None:
                psl_debug_counts.set_text("Loading production debug...")
                psl_debug_raw.value = ""
                psl_debug_options.value = ""
                psl_debug_master.value = ""
                psl_debug_raw.update()
                psl_debug_options.update()
                psl_debug_master.update()

                psl_debug_timer["start"] = time.time()
                psl_debug_timer["running"] = True
                psl_debug_timer_label.set_text("Elapsed: 0s")
                try:
                    ok_master, payload_master = await _request_json(
                        "get", "/api/productions/fetch", request, timeout=30.0
                    )
                    ok_dbs, payload_dbs = await _request_json(
                        "get", "/api/locations/production_dbs", request, timeout=30.0
                    )
                finally:
                    if psl_debug_timer["start"] is not None:
                        elapsed = int(time.time() - psl_debug_timer["start"])
                        psl_debug_timer_label.set_text(f"Elapsed: {elapsed}s")
                    psl_debug_timer["running"] = False

                master_rows = payload_master.get("data") if ok_master else []
                db_rows = payload_dbs.get("data") if ok_dbs else []

                with_locations = [row for row in master_rows if row.get("LocationsTable")]
                missing_locations = [row for row in master_rows if not row.get("LocationsTable")]

                state["productions_master"] = master_rows
                state["productions_missing_locations"] = missing_locations

                summary = (
                    f"production_dbs_returned={len(db_rows)} "
                    f"master_total={len(master_rows)} "
                    f"with_locations_table={len(with_locations)} "
                    f"missing_locations_table={len(missing_locations)}"
                )
                psl_debug_counts.set_text(summary)

                psl_debug_raw.value = format_json(db_rows, empty_message="No /api/locations/production_dbs data.")
                psl_debug_raw.update()

                psl_debug_options.value = format_json(
                    {
                        "production_select_options": state.get("productions") or [],
                        "psl_select_options": state.get("psl_options") or [],
                        "missing_locations_table": missing_locations,
                    },
                    empty_message="No options loaded. Run Load productions.",
                )
                psl_debug_options.update()

                psl_debug_master.value = format_json(master_rows, empty_message="No /api/productions/fetch data.")
                psl_debug_master.update()

            ui.button(
                "Load Production Debug",
                icon="visibility",
                on_click=lambda e: start_task(load_production_debug()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mt-2")

        # Section 8 - Generate Medical Facilities
        with ui.expansion("Generate Medical Facilities", icon="local_hospital").classes(
            "border border-slate-200 dark:border-slate-700"
        ):
            ui.label(
                "Finds nearby ER and Urgent Care locations and links them to each Locations Master row."
            ).classes("text-sm text-slate-500")
            medfac_timer = {"start": None, "running": False}
            medfac_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

            medfac_output = ui.textarea(
                value="Run to generate medical facilities for all eligible Locations Master rows.\n"
                "Output shows counts only.",
                placeholder="Generation output...",
            ).classes("w-full text-sm h-32")
            medfac_output.props("readonly")

            def _update_medfac_timer() -> None:
                if not medfac_timer["running"] or medfac_timer["start"] is None:
                    return
                elapsed = int(time.time() - medfac_timer["start"])
                medfac_timer_label.set_text(f"Elapsed: {elapsed}s")

            ui.timer(1.0, _update_medfac_timer, active=True)

            async def run_medfac_stream() -> None:
                medfac_output.value = "Starting medical facilities generation...\n"
                medfac_output.update()
                medfac_btn.disable()
                medfac_timer["start"] = time.time()
                medfac_timer["running"] = True
                medfac_timer_label.set_text("Elapsed: 0s")
                try:
                    async with httpx.AsyncClient(base_url=str(request.base_url), timeout=None) as client:
                        async with client.stream("GET", "/api/medicalfacilities/generate_all_stream") as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if line is None:
                                    continue
                                medfac_output.value += line
                                if not line.endswith("\n"):
                                    medfac_output.value += "\n"
                                medfac_output.update()
                except Exception as exc:  # noqa: BLE001
                    medfac_output.value += f"error: {exc}\n"
                    medfac_output.update()
                    ui.notify(f"Medical facilities generation failed: {exc}", type="negative", position="top")
                finally:
                    if medfac_timer["start"] is not None:
                        elapsed = int(time.time() - medfac_timer["start"])
                        medfac_timer_label.set_text(f"Elapsed: {elapsed}s")
                    medfac_timer["running"] = False
                    medfac_btn.enable()

            medfac_btn = ui.button(
                "Generate Medical Facilities (All Eligible Locations)",
                icon="play_circle",
                on_click=lambda e: start_task(run_medfac_stream()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mt-2")

        # Section 8.5 - Medical Facilities Maintenance
        with ui.expansion("Medical Facilities Maintenance", icon="build").classes(
            "border border-slate-200 dark:border-slate-700"
        ):
            ui.label(
                "Backfills missing Medical Facilities fields from Google (fills blanks only)."
            ).classes("text-sm text-slate-500")
            medfac_maint_timer = {"start": None, "running": False}
            medfac_maint_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

            medfac_maint_output = ui.textarea(
                value="Run to backfill missing Medical Facilities fields from Google (no overwrites).",
                placeholder="Maintenance output...",
            ).classes("w-full text-sm h-32")
            medfac_maint_output.props("readonly")

            def _update_medfac_maint_timer() -> None:
                if not medfac_maint_timer["running"] or medfac_maint_timer["start"] is None:
                    return
                elapsed = int(time.time() - medfac_maint_timer["start"])
                medfac_maint_timer_label.set_text(f"Elapsed: {elapsed}s")

            ui.timer(1.0, _update_medfac_maint_timer, active=True)

            async def run_medfac_maintenance_stream() -> None:
                medfac_maint_output.value = "Starting Medical Facilities maintenance...\n"
                medfac_maint_output.update()
                medfac_maint_btn.disable()
                medfac_maint_timer["start"] = time.time()
                medfac_maint_timer["running"] = True
                medfac_maint_timer_label.set_text("Elapsed: 0s")
                try:
                    async with httpx.AsyncClient(base_url=str(request.base_url), timeout=None) as client:
                        async with client.stream("GET", "/api/medicalfacilities/maintenance_stream") as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if line is None:
                                    continue
                                medfac_maint_output.value += line
                                if not line.endswith("\n"):
                                    medfac_maint_output.value += "\n"
                                medfac_maint_output.update()
                except Exception as exc:  # noqa: BLE001
                    medfac_maint_output.value += f"error: {exc}\n"
                    medfac_maint_output.update()
                    ui.notify(f"MF maintenance failed: {exc}", type="negative", position="top")
                finally:
                    if medfac_maint_timer["start"] is not None:
                        elapsed = int(time.time() - medfac_maint_timer["start"])
                        medfac_maint_timer_label.set_text(f"Elapsed: {elapsed}s")
                    medfac_maint_timer["running"] = False
                    medfac_maint_btn.enable()

            medfac_maint_btn = ui.button(
                "Backfill Missing MF Fields",
                icon="build",
                on_click=lambda e: start_task(run_medfac_maintenance_stream()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mt-2")

        # Section 9 - Dedup Simple Admin
        with ui.expansion("Dedup Simple Admin", icon="tune").classes("border border-slate-200 dark:border-slate-700"):
            ui.label(
                "Scans Locations Master for duplicates and streams a dedup summary."
            ).classes("text-sm text-slate-500")
            dedup_timer = {"start": None, "running": False}
            dedup_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

            dedup_output = ui.textarea(
                value="Dedup results will stream here.",
                placeholder="Streaming dedup scan...",
            ).classes("w-full text-sm h-40")
            dedup_output.props("readonly")

            def _update_dedup_timer() -> None:
                if not dedup_timer["running"] or dedup_timer["start"] is None:
                    return
                elapsed = int(time.time() - dedup_timer["start"])
                dedup_timer_label.set_text(f"Elapsed: {elapsed}s")

            ui.timer(1.0, _update_dedup_timer, active=True)

            async def run_dedup_stream() -> None:
                dedup_output.value = "Starting dedup scan...\n"
                dedup_output.update()
                dedup_btn.disable()
                dedup_timer["start"] = time.time()
                dedup_timer["running"] = True
                dedup_timer_label.set_text("Elapsed: 0s")
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
                    if dedup_timer["start"] is not None:
                        elapsed = int(time.time() - dedup_timer["start"])
                        dedup_timer_label.set_text(f"Elapsed: {elapsed}s")
                    dedup_timer["running"] = False
                    dedup_btn.enable()

            dedup_btn = ui.button(
                "Run Dedup Scan",
                icon="refresh",
                on_click=lambda e: start_task(run_dedup_stream()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mt-2")

        # Section 9 - Diagnostics (streaming)
        with ui.expansion("Diagnostics", icon="bug_report").classes("border border-slate-200 dark:border-slate-700"):
            ui.label(
                "Runs a health check across key services and streams diagnostic output."
            ).classes("text-sm text-slate-500")
            diag_timer = {"start": None, "running": False}
            diag_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

            diag_output = ui.textarea(
                value="Diagnostics output will stream here.",
                placeholder="Streaming diagnostics...",
            ).classes("w-full text-sm h-40")
            diag_output.props("readonly")

            def _update_diag_timer() -> None:
                if not diag_timer["running"] or diag_timer["start"] is None:
                    return
                elapsed = int(time.time() - diag_timer["start"])
                diag_timer_label.set_text(f"Elapsed: {elapsed}s")

            ui.timer(1.0, _update_diag_timer, active=True)

            async def run_diagnostics() -> None:
                diag_output.value = "Starting diagnostics...\n"
                diag_output.update()
                diag_btn.disable()
                diag_timer["start"] = time.time()
                diag_timer["running"] = True
                diag_timer_label.set_text("Elapsed: 0s")
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
                    if diag_timer["start"] is not None:
                        elapsed = int(time.time() - diag_timer["start"])
                        diag_timer_label.set_text(f"Elapsed: {elapsed}s")
                    diag_timer["running"] = False
                    diag_btn.enable()

            diag_btn = ui.button(
                "Run Diagnostics",
                icon="bug_report",
                on_click=lambda e: start_task(run_diagnostics()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1")

        # Section 9 - System Info
        with ui.expansion("System Info", icon="info").classes("border border-slate-200 dark:border-slate-700"):
            ui.label(
                "Loads current system configuration and runtime environment details."
            ).classes("text-sm text-slate-500")
            sys_timer = {"start": None, "running": False}
            sys_timer_label = ui.label("Elapsed: 0s").classes("text-sm text-slate-500")

            sys_output = ui.code("System info will appear here.").classes("w-full text-sm")

            def _update_sys_timer() -> None:
                if not sys_timer["running"] or sys_timer["start"] is None:
                    return
                elapsed = int(time.time() - sys_timer["start"])
                sys_timer_label.set_text(f"Elapsed: {elapsed}s")

            ui.timer(1.0, _update_sys_timer, active=True)

            async def load_system_info() -> None:
                sys_output.content = "Loading system info..."
                sys_output.update()
                sys_timer["start"] = time.time()
                sys_timer["running"] = True
                sys_timer_label.set_text("Elapsed: 0s")
                ok, payload = await _request_json("get", "/api/locations/system_info", request)
                if not ok:
                    sys_output.content = f"error: {payload.get('error')}"
                    sys_output.update()
                    if sys_timer["start"] is not None:
                        elapsed = int(time.time() - sys_timer["start"])
                        sys_timer_label.set_text(f"Elapsed: {elapsed}s")
                    sys_timer["running"] = False
                    return
                sys_output.content = format_json(payload)
                sys_output.update()
                if sys_timer["start"] is not None:
                    elapsed = int(time.time() - sys_timer["start"])
                    sys_timer_label.set_text(f"Elapsed: {elapsed}s")
                sys_timer["running"] = False

            ui.button(
                "Load System Info",
                icon="info",
                on_click=lambda e: start_task(load_system_info()),
            ).classes("bg-slate-900 text-white hover:bg-slate-800 px-3 py-1 mt-2")

    # no production-scoped tools remain on this page
