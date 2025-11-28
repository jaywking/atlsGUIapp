import asyncio
from typing import Any, Dict, List
from urllib.parse import urljoin, urlsplit

import httpx
from nicegui import ui

from app.ui.layout import PAGE_HEADER_CLASSES


def _build_origin() -> str:
    try:
        base_url = str(ui.context.client.request.base_url)
    except Exception:
        base_url = "http://127.0.0.1:8001/"
    parsed = urlsplit(base_url)
    scheme = parsed.scheme or "http"
    netloc = parsed.hostname or "127.0.0.1"
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return f"{scheme}://{netloc}/"


async def fetch_groups(origin: str, debug) -> List[Dict[str, Any]]:
    url = urljoin(origin, "api/locations/master/dedup?refresh=true")
    debug(f"Calling dedup list at {url}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json() or {}
    if isinstance(data, dict):
        return data.get("duplicate_groups") or []
    if isinstance(data, list):
        return data
    return []


async def fetch_preview(origin: str, group_id: str) -> Dict[str, Any]:
    url = urljoin(origin, f"api/locations/master/dedup_resolve_preview?group_id={group_id}")
    print(f"[dedup_ui] fetch_preview url={url}")
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url)
    try:
        resp.raise_for_status()
        data = resp.json() or {}
        if isinstance(data, dict) and data.get("status") == "error":
            return {"status": "error", "message": data.get("message") or "Preview failed", "url": url}
        return {"status": "success", "data": data, "url": url}
    except httpx.HTTPStatusError as exc:
        return {"status": "error", "message": f"HTTP {exc.response.status_code}: {exc.response.text}", "url": url}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Preview error: {exc}", "url": url}


async def apply_merge(origin: str, group_id: str, primary_id: str, duplicate_ids: List[str]) -> Dict[str, Any]:
    payload = {"group_id": group_id, "primary_id": primary_id, "duplicate_ids": duplicate_ids}
    url = urljoin(origin, "api/locations/master/dedup_resolve_apply")
    print(f"[dedup_ui] apply_merge url={url} payload={payload}")
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload)
    try:
        resp.raise_for_status()
        data = resp.json() or {}
        if isinstance(data, dict) and data.get("status") == "error":
            return {"status": "error", "message": data.get("message") or "Apply failed", "url": url}
        return {"status": "success", "data": data, "url": url}
    except httpx.HTTPStatusError as exc:
        return {"status": "error", "message": f"HTTP {exc.response.status_code}: {exc.response.text}", "url": url}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Apply error: {exc}", "url": url}


def page_content() -> None:
    status_label = ui.label("").classes("text-sm text-slate-500")
    spinner = ui.spinner(type="dots").props("size=24 color=primary").classes("mt-2")
    group_container = ui.column().classes("w-full gap-3")
    debug_log = ui.label("").classes("text-xs text-slate-500")

    def debug(msg: str) -> None:
        print(f"[dedup_ui] {msg}")
        debug_log.set_text(msg)

    origin = _build_origin()
    debug(f"API origin set to {origin}")

    async def load_groups() -> None:
        spinner.visible = True
        status_label.set_text("Loading duplicate groups...")
        group_container.clear()
        try:
            groups = await fetch_groups(origin, debug)
            debug(f"Loaded groups payload: {groups}")
            if not groups:
                status_label.set_text("No duplicate groups found.")
                return
            status_label.set_text(f"Loaded {len(groups)} duplicate groups.")
            for g in groups:
                gid = g.get("group_id") or g.get("groupId")
                reason = g.get("reason")
                size = len(g.get("rows", []))
                with group_container:
                    with ui.row().classes("w-full items-center justify-between border border-slate-200 dark:border-slate-700 rounded px-3 py-2"):
                        ui.label(f"{gid}").classes("font-semibold")
                        ui.label(f"Reason: {reason}").classes("text-sm")
                        ui.label(f"Rows: {size}").classes("text-sm")
                        def _handler(group_id: str):
                            debug(f"Preview clicked for {group_id}")
                            ui.run_task(open_preview(group_id))

                        ui.button(
                            "Preview",
                            on_click=lambda e=None, group_id=gid: _handler(group_id),
                        ).classes("bg-amber-500 text-white hover:bg-amber-600 px-3 py-1 rounded")
        except Exception as exc:  # noqa: BLE001
            status_label.set_text(f"Failed to load groups: {exc}")
            ui.notify(f"Failed to load groups: {exc}", type="negative", position="top")
            debug(f"load_groups error: {exc}")
        finally:
            spinner.visible = False

    async def do_apply(preview: Dict[str, Any], dialog: ui.dialog, apply_button: ui.button) -> None:
        apply_button.disable()
        apply_button.props("loading")
        try:
            result = await apply_merge(
                origin,
                preview.get("group_id"),
                preview.get("primary_id"),
                preview.get("duplicate_ids") or [],
            )
            ui.notify(f"Merge applied: {result.get('summary')}", type="positive", position="top")
            dialog.close()
            await load_groups()
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Apply failed: {exc}", type="negative", position="top")
        finally:
            apply_button.enable()
            apply_button.props(remove="loading")

    async def open_preview(group_id: str) -> None:
        if not group_id:
            ui.notify("Missing group id for preview", type="negative", position="top")
            return
        ui.notify(f"Loading preview for {group_id}...", type="info", position="top", timeout=1.5)
        debug(f"fetching preview for {group_id}")
        preview_resp = await fetch_preview(origin, group_id)
        if preview_resp.get("status") == "error":
            msg = preview_resp.get("message") or "Preview failed"
            ui.notify(msg, type="negative", position="top")
            debug(f"preview failed for {group_id}: {msg} (url={preview_resp.get('url')})")
            return
        preview = preview_resp.get("data") or {}
        debug(f"preview success for {group_id} (url={preview_resp.get('url')})")
        ui.notify(f"Preview loaded for {group_id}", type="positive", position="top", timeout=1.5)

        try:
            dialog = ui.dialog()
            with dialog, ui.card():
                debug(f"rendering preview modal for {group_id}")
                ui.label(f"Group {group_id} Preview").classes("text-lg font-semibold mb-2")
                ui.label(f"Primary: {preview.get('primary_id', '')}").classes("font-semibold")
                ui.label("Duplicates:").classes("mt-2 text-sm font-semibold")
                for dup in preview.get("duplicate_ids", []):
                    ui.label(dup).classes("text-sm")

                ui.label("Field Updates").classes("mt-3 text-sm font-semibold")
                updates = preview.get("field_updates") or {}
                if updates:
                    for k, v in updates.items():
                        ui.label(f"{k}: {v}").classes("text-sm")
                else:
                    ui.label("None").classes("text-sm")

                ui.label("Production Pointer Updates").classes("mt-3 text-sm font-semibold")
                prod_updates = preview.get("prod_loc_updates") or []
                if prod_updates:
                    for upd in prod_updates:
                        ui.label(f"{upd.get('prod_loc_id')} -> {upd.get('new_master_id')} (old {upd.get('old_master_id')})").classes("text-sm")
                else:
                    ui.label("None").classes("text-sm")

                ui.label("Rows to Archive").classes("mt-3 text-sm font-semibold")
                delete_ids = preview.get("delete_master_ids") or []
                if delete_ids:
                    for did in delete_ids:
                        ui.label(did).classes("text-sm")
                else:
                    ui.label("None").classes("text-sm")

                ui.label(preview.get("summary", "")).classes("mt-3 text-sm")

                with ui.row().classes("w-full justify-end gap-2 mt-3"):
                    ui.button("Cancel", on_click=dialog.close).classes("px-3 py-1")
                    apply_btn = ui.button(
                        "Apply Merge",
                        on_click=lambda e=None: ui.run_task(do_apply(preview, dialog, apply_btn)),
                    ).classes("px-3 py-1 bg-red-600 text-white hover:bg-red-700")

            dialog.open()
            debug(f"dialog opened for {group_id}")
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Preview render failed: {exc}", type="negative", position="top")
            debug(f"preview render failed for {group_id}: {exc}")

    with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px]"):
        ui.label("Locations Master - Dedup Resolution").classes("text-xl font-semibold")
        ui.button("Refresh", on_click=lambda e=None: asyncio.create_task(load_groups())).classes("px-3 py-1")

    ui.separator()
    status_label
    spinner
    group_container
    debug_log

    asyncio.create_task(load_groups())
