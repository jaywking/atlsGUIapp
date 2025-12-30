"""NiceGUI dashboard landing page."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List
from datetime import datetime, timezone

import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui.layout import PAGE_HEADER_CLASSES


SUMMARY_ENDPOINT = "/api/dashboard/summary"


def page_content() -> None:
    """Render the dashboard shell with async data loading."""

    with ui.row().classes(f"{PAGE_HEADER_CLASSES} atls-header-tight min-h-[52px] justify-between items-center"):
        with ui.row().classes('items-center gap-2 flex-wrap'):
            status_spinner = ui.spinner(size='sm').style('display: none;')
            header_refresh = ui.button('Refresh Overview').classes('bg-slate-800 text-white hover:bg-slate-900 dark:hover:bg-slate-800')
        ui.space()

    with ui.row().classes('gap-3 w-full flex-wrap'):
        production_card = _metric_card('Productions', '0')
        location_card = _metric_card('Locations', '0')
        notion_status = _status_card('Notion API', 'unknown')
        maps_status = _status_card('Google Maps', 'unknown')

    with ui.card().classes('w-full shadow-sm border border-slate-200 mt-3'):
        with ui.row().classes('items-center justify-between w-full mb-2'):
            ui.label('Recent Jobs (last 24h)').classes('text-base font-semibold')
        error_label = ui.label('').classes('text-sm text-red-600').style('display: none;')
        jobs_spinner = ui.spinner(size='md').style('display: none; margin-bottom: 12px;')
        with ui.element('div').classes('w-full overflow-x-auto py-1'):
            jobs_table = ui.table(
                columns=[
                    {'name': 'timestamp', 'label': 'Timestamp', 'field': 'timestamp', 'sortable': True},
                    {'name': 'category', 'label': 'Category', 'field': 'category', 'sortable': True},
                    {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True},
                    {'name': 'message', 'label': 'Message', 'field': 'message'},
                ],
                rows=[],
            ).classes('w-full text-sm').props('flat square wrap-cells dense')

    with ui.row().classes('gap-3 mt-4 flex-wrap'):
        ui.button(
            'Go to Productions', on_click=lambda: ui.navigate.to('/productions')
        ).classes('bg-slate-800 text-white hover:bg-slate-900 dark:hover:bg-slate-800')
        ui.button(
            'Go to Locations', on_click=lambda: ui.navigate.to('/locations')
        ).classes('bg-slate-800 text-white hover:bg-slate-900 dark:hover:bg-slate-800')
        ui.button('Go to Jobs', on_click=lambda: ui.navigate.to('/jobs')).classes(
            'bg-slate-800 text-white hover:bg-slate-900 dark:hover:bg-slate-800'
        )
        ui.button('Go to Settings', on_click=lambda: ui.navigate.to('/settings')).classes(
            'bg-slate-800 text-white hover:bg-slate-900 dark:hover:bg-slate-800'
        )

    async def refresh() -> None:
        await _load_summary(
            production_card,
            location_card,
            notion_status,
            maps_status,
            jobs_table,
            status_spinner,
            jobs_spinner,
            error_label,
        )

    header_refresh.on('click', lambda: asyncio.create_task(refresh()))
    ui.timer(0.2, lambda: asyncio.create_task(refresh()), once=True)


def _metric_card(title: str, initial_value: str):
    with ui.card().classes(
        'min-w-[180px] flex-1 shadow-sm border border-slate-200 '
        'flex flex-col gap-1 min-h-[88px] px-3 py-2 justify-center'
    ) as card:
        ui.label(title).classes('text-sm font-medium text-slate-600')
        value_label = ui.label(initial_value).classes('text-2xl font-semibold text-slate-900')
    card.value_label = value_label  # type: ignore[attr-defined]
    return card


def _status_card(title: str, status: str):
    with ui.card().classes(
        'min-w-[180px] flex-1 shadow-sm border border-slate-200 '
        'flex flex-col gap-1 min-h-[88px] px-3 py-2 justify-center'
    ) as card:
        ui.label(title).classes('text-sm font-medium text-slate-600')
        status_label = ui.label(_format_status_text(status)).classes(_status_classes(status))
    card.status_label = status_label  # type: ignore[attr-defined]
    return card


async def _load_summary(
    production_card,
    location_card,
    notion_status,
    maps_status,
    jobs_table,
    status_spinner,
    jobs_spinner,
    error_label,
) -> None:
    status_spinner.style('display: inline-block;')
    jobs_spinner.style('display: inline-block; margin-bottom: 12px;')
    error_label.style('display: none;')
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(api_url(SUMMARY_ENDPOINT))
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # noqa: BLE001
        error_label.text = f'Unable to load dashboard: {exc}'
        error_label.style('display: block;')
        return
    finally:
        status_spinner.style('display: none;')
        jobs_spinner.style('display: none;')

    _update_metric_card(production_card, data.get('productions_total', 0))
    _update_metric_card(location_card, data.get('locations_total', 0))
    _update_status_card(notion_status, data.get('notion_status', 'unknown'))
    _update_status_card(maps_status, data.get('maps_status', 'unknown'))
    _populate_jobs_table(jobs_table, data.get('recent_jobs', []))


def _update_metric_card(card, value: Any) -> None:
    label = getattr(card, 'value_label', None)
    if label is not None:
        label.text = f'{value}'


def _update_status_card(card, status: str) -> None:
    label = getattr(card, 'status_label', None)
    if label is None:
        return
    label.text = _format_status_text(status)
    label.classes.clear()
    label.classes(_status_classes(status))


def _format_status_text(status: str) -> str:
    if not status:
        return 'Unknown'
    return status.replace('_', ' ').replace('-', ' ').title()


def _status_classes(status: str) -> str:
    normalized = (status or '').lower()
    if normalized == 'connected':
        return 'text-green-600 font-semibold text-xl'
    if normalized in {'missing-token', 'missing-key'}:
        return 'text-amber-600 font-semibold text-xl'
    return 'text-red-600 font-semibold text-xl'


def _populate_jobs_table(table, jobs: List[Dict[str, Any]]) -> None:
    if not isinstance(jobs, list):
        jobs = []
    rows: List[Dict[str, Any]] = []
    for idx, job in enumerate(jobs):
        raw_ts = job.get('timestamp', '--')
        ts_display = _format_local_timestamp(raw_ts)
        rows.append(
            {
                'id': f"job-{idx}",
                'timestamp': ts_display,
                'category': job.get('category', '--'),
                'status': (job.get('status') or 'unknown').title(),
                'message': job.get('message', ''),
            }
        )
    table.rows = rows


def _format_local_timestamp(raw: Any) -> str:
    """Convert ISO8601 UTC (e.g., 2025-11-09T21:44:52Z) to local time.

    Output format: "YYYY-MM-DD - HH:MM:SS". Falls back gracefully when parsing
    fails or when value is missing.
    """
    if not isinstance(raw, str) or not raw:
        return '--'
    try:
        iso = raw
        if iso.endswith('Z'):
            iso = iso[:-1] + '+00:00'
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local_dt = dt.astimezone()  # convert to local timezone
        return local_dt.strftime('%Y-%m-%d - %H:%M:%S')
    except Exception:
        return raw

