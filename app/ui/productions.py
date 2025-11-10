from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import requests
from nicegui import ui

from app.services.api_client import api_url


def page_content() -> None:
    ui.label('Productions').classes('text-xl font-semibold')
    ui.label('Live view of productions stored in Notion.').classes('text-slate-500 mb-4')

    state: Dict[str, Any] = {"rows": []}

    with ui.row().classes('items-center gap-3 w-full flex-wrap'):
        refresh_button = ui.button('Refresh').classes('bg-blue-500 text-white')
        sync_button = ui.button('Sync Now').classes('bg-slate-800 text-white')
        spinner = ui.spinner(size='md').style('display: none;')
        status_label = ui.label('No data loaded yet.').classes('text-sm text-slate-500')

    columns = [
        {'name': 'title', 'label': 'Title', 'field': 'title', 'sortable': True},
        {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True},
        {'name': 'start_date', 'label': 'Start Date', 'field': 'start_date', 'sortable': True},
        {'name': 'last_updated', 'label': 'Last Updated', 'field': 'last_updated', 'sortable': True},
    ]

    table = (
        ui.table(columns=columns, rows=[], row_key='row_id')
        .classes('w-full text-sm')
        .props('flat wrap-cells square')
    )

    def set_loading(is_loading: bool) -> None:
        spinner.style('display: inline-block;' if is_loading else 'display: none;')
        refresh_button.set_enabled(not is_loading)
        sync_button.set_enabled(not is_loading)

    def update_table(rows: List[Dict[str, Any]]) -> None:
        table_rows = []
        for idx, row in enumerate(rows):
            table_rows.append(
                {
                    'row_id': row.get('id') or f'row-{idx}',
                    'title': row.get('title') or 'Untitled',
                    'status': row.get('status') or '--',
                    'start_date': row.get('start_date_display') or '--',
                    'last_updated': row.get('last_updated_display') or '--',
                }
            )
        table.rows = table_rows

    def fetch_data(show_toast: bool = False) -> None:
        set_loading(True)
        try:
            response = requests.get(api_url("/api/productions/fetch"), timeout=20)
            response.raise_for_status()
            payload = response.json()
            if payload.get('status') != 'success':
                raise ValueError(payload.get('message', 'Unable to fetch productions'))
            raw_rows = payload.get('data', [])
            state['rows'] = [_decorate_row(row) for row in raw_rows]
            update_table(state['rows'])
            message = payload.get('message', f'Loaded {len(state["rows"])} productions')
            status_label.text = message
            status_label.classes('text-sm text-slate-500')
            if show_toast:
                ui.notify(message, type='positive')
        except Exception as exc:  # noqa: BLE001
            status_label.text = f'Error: {exc}'
            status_label.classes('text-sm text-red-600')
            ui.notify(f'Failed to load productions: {exc}', type='negative')
        finally:
            set_loading(False)

    def sync_now() -> None:
        if not state['rows']:
            ui.notify('Nothing to sync yet. Please refresh first.', type='warning')
            return
        set_loading(True)
        try:
            payload = {
                'updates': [
                    {
                        'id': row.get('id'),
                        'status': row.get('status'),
                        'start_date': row.get('start_date'),
                    }
                    for row in state['rows']
                    if row.get('id')
                ]
            }
            response = requests.post(api_url("/api/productions/sync"), json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('status') != 'success':
                raise ValueError(data.get('message', 'Sync failed'))
            ui.notify(data.get('message', 'Sync completed'), type='positive')
            fetch_data()
        except Exception as exc:  # noqa: BLE001
            status_label.text = f'Sync failed: {exc}'
            status_label.classes('text-sm text-red-600')
            ui.notify(f'Sync failed: {exc}', type='negative')
            set_loading(False)

    def _decorate_row(row: Dict[str, Any]) -> Dict[str, Any]:
        start_iso = row.get('start_date')
        last_iso = row.get('last_updated')
        return {
            **row,
            'start_date_display': _format_local_date(start_iso),
            'last_updated_display': _format_local_timestamp(last_iso),
        }

    refresh_button.on('click', lambda _: fetch_data(show_toast=True))
    sync_button.on('click', lambda _: sync_now())

    fetch_data()


def _format_local_date(raw: Any) -> str:
    if not raw:
        return '--'
    try:
        if isinstance(raw, str) and len(raw) == 10:
            dt = datetime.strptime(raw, "%Y-%m-%d")
        else:
            dt = datetime.fromisoformat(str(raw).replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return str(raw)


def _format_local_timestamp(raw: Any) -> str:
    if not raw:
        return '--'
    try:
        dt = datetime.fromisoformat(str(raw).replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local_dt = dt.astimezone()
        return local_dt.strftime('%Y-%m-%d - %H:%M:%S')
    except ValueError:
        return str(raw)
