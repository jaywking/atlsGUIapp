"""NiceGUI dashboard landing page."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx
from nicegui import ui

from app.services.api_client import api_url


SUMMARY_ENDPOINT = "/api/dashboard/summary"


def page_content() -> None:
    """Render the dashboard shell with async data loading."""

    ui.label('Operations Dashboard').classes('text-xl font-semibold')
    ui.label('Snapshot of productions, locations, and system health.').classes(
        'text-slate-500 mb-4'
    )

    with ui.row().classes('gap-4 w-full flex-wrap'):
        production_card = _metric_card('Productions', '0')
        location_card = _metric_card('Locations', '0')
        notion_status = _status_card('Notion API', 'unknown')
        maps_status = _status_card('Google Maps', 'unknown')

    with ui.card().classes('w-full shadow-sm border border-slate-200 mt-4'):
        with ui.row().classes('items-center justify-between w-full mb-3'):
            ui.label('Recent Jobs (last 24h)').classes('text-lg font-semibold')
            refresh_button = ui.button('Refresh').classes('bg-blue-500 text-white px-4')
        error_label = ui.label('').classes('text-sm text-red-600').style('display: none;')
        spinner = ui.spinner(size='md').style('display: none; margin-bottom: 12px;')
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
        ).classes('bg-slate-800 text-white')
        ui.button(
            'Go to Locations', on_click=lambda: ui.navigate.to('/locations')
        ).classes('bg-slate-800 text-white')
        ui.button('Go to Jobs', on_click=lambda: ui.navigate.to('/jobs')).classes(
            'bg-slate-800 text-white'
        )
        ui.button('Go to Settings', on_click=lambda: ui.navigate.to('/settings')).classes(
            'bg-slate-800 text-white'
        )

    async def refresh() -> None:
        await _load_summary(
            production_card,
            location_card,
            notion_status,
            maps_status,
            jobs_table,
            spinner,
            error_label,
        )

    refresh_button.on('click', lambda: asyncio.create_task(refresh()))
    ui.timer(0.2, lambda: asyncio.create_task(refresh()), once=True)


def _metric_card(title: str, initial_value: str):
    with ui.card().classes('min-w-[200px] flex-1 shadow-sm border border-slate-200') as card:
        ui.label(title).classes('text-sm text-slate-500')
        value_label = ui.label(initial_value).classes('text-3xl font-semibold text-slate-900')
    card.value_label = value_label  # type: ignore[attr-defined]
    return card


def _status_card(title: str, status: str):
    with ui.card().classes('min-w-[200px] flex-1 shadow-sm border border-slate-200') as card:
        ui.label(title).classes('text-sm text-slate-500')
        status_label = ui.label(_format_status_text(status)).classes(_status_classes(status))
    card.status_label = status_label  # type: ignore[attr-defined]
    return card


async def _load_summary(
    production_card,
    location_card,
    notion_status,
    maps_status,
    jobs_table,
    spinner,
    error_label,
) -> None:
    spinner.style('display: inline-block; margin-bottom: 12px;')
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
        spinner.style('display: none;')

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
        return 'text-green-600 font-semibold text-lg'
    if normalized in {'missing-token', 'missing-key'}:
        return 'text-amber-600 font-semibold text-lg'
    return 'text-red-600 font-semibold text-lg'


def _populate_jobs_table(table, jobs: List[Dict[str, Any]]) -> None:
    if not isinstance(jobs, list):
        jobs = []
    rows: List[Dict[str, Any]] = []
    for idx, job in enumerate(jobs):
        rows.append(
            {
                'id': f"job-{idx}",
                'timestamp': job.get('timestamp', '--'),
                'category': job.get('category', '--'),
                'status': (job.get('status') or 'unknown').title(),
                'message': job.get('message', ''),
            }
        )
    table.rows = rows

