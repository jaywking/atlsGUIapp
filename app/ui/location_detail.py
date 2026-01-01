from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui.layout import PAGE_HEADER_CLASSES


def _format_local_timestamp(raw: str) -> str:
    if not raw:
        return "--"
    try:
        value = raw
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return raw


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


def page_content(master_id: str) -> None:
    state: Dict[str, Any] = {"location": None, "productions": []}

    title_label = ui.label("Location Details").classes("text-xl font-semibold")
    subtitle_label = ui.label(master_id).classes("text-sm text-slate-500")

    with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px] items-center justify-between"):
        with ui.column().classes("w-full"):
            title_label
            subtitle_label

    with ui.row().classes("items-center gap-2"):
        loading_spinner = ui.spinner(size="md").props("color=primary")
        status_label = ui.label("Loading location details...").classes("text-sm text-slate-500")

    summary_block = ui.expansion("Summary", icon="summarize", value=True).classes("w-full")
    address_block = ui.expansion("Address & Geography", icon="place", value=False).classes("w-full")
    med_block = ui.expansion("Medical Facilities", icon="local_hospital", value=False).classes("w-full")
    usage_block = ui.expansion("Production Usage", icon="work", value=False).classes("w-full")
    class_block = ui.expansion("Classification & Status", icon="label", value=False).classes("w-full")
    meta_block = ui.expansion("Metadata", icon="info", value=False).classes("w-full")

    async def load_detail() -> None:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(api_url("/api/locations/detail"), params={"master_id": master_id})
            response.raise_for_status()
            payload = response.json() or {}
            if payload.get("status") != "success":
                raise ValueError(payload.get("message") or "Location not found")
            data = payload.get("data") or {}
            state["location"] = data.get("location") or {}
            state["productions"] = data.get("productions") or []
        except Exception as exc:  # noqa: BLE001
            loading_spinner.set_visibility(False)
            status_label.set_text(f"Location not found: {exc}")
            return

        loading_spinner.set_visibility(False)
        status_label.set_text("")

        loc = state["location"] or {}
        productions: List[Dict[str, str]] = state["productions"] or []
        facilities = data.get("medical_facilities") or {}

        title_label.set_text(loc.get("practical_name") or loc.get("name") or master_id)
        subtitle_label.set_text("")

        summary_block.clear()
        with summary_block:
            with ui.row().classes("w-full gap-6 flex-wrap"):
                with ui.column().classes("flex-1 min-w-[260px] gap-2"):
                    with ui.row().classes("w-full items-start gap-2"):
                        ui.label("Location Master ID").classes("text-sm text-slate-500 w-48 shrink-0")
                        master_value = loc.get("master_id", "") or "--"
                        notion_url = loc.get("notion_url") or ""
                        if notion_url:
                            ui.link(master_value, notion_url).props("target=_blank").classes(
                                "text-sm text-slate-900 hover:underline"
                            )
                        else:
                            ui.label(master_value).classes("text-sm text-slate-900 dark:text-slate-200")
                    _render_kv("Practical Name", loc.get("practical_name", "") or loc.get("name", ""))
                    _render_kv("Full Address", loc.get("full_address", ""))
                    _render_kv(
                        "City / State / Country",
                        f"{loc.get('city', '')}, {loc.get('state', '')} {loc.get('country', '')}".strip(", "),
                    )
                with ui.column().classes("flex-1 min-w-[260px] gap-2"):
                    types = ", ".join(loc.get("place_types") or []) or "--"
                    _render_kv("Place Type", types)
                    with ui.row().classes("w-full items-start gap-2"):
                        ui.label("Google Maps").classes("text-sm text-slate-500 w-48 shrink-0")
                        url = loc.get("google_maps_url") or ""
                        if url:
                            ui.link("Open Map", url).props("target=_blank").classes("text-sm text-slate-900 hover:underline")
                        else:
                            ui.label("--").classes("text-sm text-slate-900 dark:text-slate-200")

        address_block.clear()
        with address_block:
            with ui.row().classes("w-full gap-6 flex-wrap"):
                with ui.column().classes("flex-1 min-w-[260px] gap-2"):
                    _render_kv("Address1", loc.get("address1", ""))
                    _render_kv("Address2", loc.get("address2", ""))
                    _render_kv("Address3", loc.get("address3", ""))
                    _render_kv("City", loc.get("city", ""))
                    _render_kv("State", loc.get("state", ""))
                    _render_kv("Zip", loc.get("zip", ""))
                with ui.column().classes("flex-1 min-w-[260px] gap-2"):
                    _render_kv("Country", loc.get("country", ""))
                    _render_kv("County", loc.get("county", ""))
                    _render_kv("Borough", loc.get("borough", ""))
                    _render_kv("Latitude", str(loc.get("latitude") or ""))
                    _render_kv("Longitude", str(loc.get("longitude") or ""))

        med_block.clear()
        with med_block:
            er = facilities.get("er")
            ucs = facilities.get("ucs") or []
            if not er and not ucs:
                ui.label("No medical facilities linked.").classes("text-sm text-slate-500")
            else:
                if er:
                    ui.label("Nearest ER").classes("text-sm font-semibold text-slate-600")
                    _render_kv("Name", er.get("name") or "")
                    _render_kv("Address", er.get("address") or "")
                    _render_kv("Phone", er.get("phone") or "")
                    with ui.row().classes("w-full items-start gap-2"):
                        ui.label("Map").classes("text-sm text-slate-500 w-48 shrink-0")
                        if er.get("google_maps_url"):
                            ui.link("Open Map", er.get("google_maps_url")).props("target=_blank").classes(
                                "text-sm text-slate-900 hover:underline"
                            )
                        else:
                            ui.label("--").classes("text-sm text-slate-900 dark:text-slate-200")
                if ucs:
                    ui.label("Nearest Urgent Care").classes("text-sm font-semibold text-slate-600 mt-2")
                    for idx, uc in enumerate(ucs, start=1):
                        ui.label(f"UC {idx}").classes("text-xs font-semibold text-slate-500")
                        _render_kv("Name", uc.get("name") or "")
                        _render_kv("Address", uc.get("address") or "")
                        _render_kv("Phone", uc.get("phone") or "")
                        with ui.row().classes("w-full items-start gap-2"):
                            ui.label("Map").classes("text-sm text-slate-500 w-48 shrink-0")
                            if uc.get("google_maps_url"):
                                ui.link("Open Map", uc.get("google_maps_url")).props("target=_blank").classes(
                                    "text-sm text-slate-900 hover:underline"
                                )
                            else:
                                ui.label("--").classes("text-sm text-slate-900 dark:text-slate-200")

        usage_block.clear()
        with usage_block:
            if not productions:
                ui.label("No productions linked.").classes("text-sm text-slate-500")
            else:
                for prod in productions:
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label(prod.get("production_name") or "Production").classes("text-sm")
                        ui.label(prod.get("production_id") or "").classes("text-sm text-slate-500")

        class_block.clear()
        with class_block:
            _render_kv("Place Types", _join_list(loc.get("place_types")))
            _render_kv("Status", loc.get("status", ""))
            _render_kv("Location Op Status", loc.get("location_op_status", ""))
            _render_kv("Place ID", loc.get("place_id", ""))

        meta_block.clear()
        with meta_block:
            _render_kv("Created", _format_local_timestamp(loc.get("created_time") or ""))
            _render_kv("Last Updated", _format_local_timestamp(loc.get("updated_time") or ""))
            _render_kv("Notion Page ID", loc.get("notion_page_id") or "")

    ui.timer(0.1, lambda: asyncio.create_task(load_detail()), once=True)
