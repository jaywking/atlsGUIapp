from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx
from nicegui import ui

from app.services.api_client import api_url


ROWS_PER_PAGE = 10
AUTO_REFRESH_SECONDS = 60

STATUS_STYLES = {
    "complete": "bg-green-100 text-green-800",
    "ready": "bg-green-100 text-green-800",
    "active": "bg-green-100 text-green-800",
    "pending": "bg-amber-100 text-amber-700",
    "planned": "bg-amber-100 text-amber-700",
    "on hold": "bg-amber-100 text-amber-700",
}


def page_content() -> None:
    ui.label('Productions').classes('text-xl font-semibold')
    ui.label('Live view of productions stored in Notion.').classes('text-slate-500 mb-4')

    state: Dict[str, Any] = {
        "rows": [],
        "filtered": [],
        "search": "",
        "page": 0,
        "auto_refresh": False,
    }

    with ui.row().classes('items-center gap-3 w-full flex-wrap'):
        refresh_button = ui.button('Refresh').classes('bg-blue-500 text-white')
        sync_button = ui.button('Sync Now').classes('bg-slate-800 text-white')
        auto_switch = ui.switch('Auto-refresh (60s)').classes('text-sm text-slate-600')
        spinner = ui.spinner(size='md').style('display: none;')
        status_label = ui.label('No data loaded yet.').classes('text-sm text-slate-500 ml-auto')

    with ui.row().classes('items-center gap-3 w-full flex-wrap'):
        search_input = ui.input(label='Search title or status...').props('dense clearable debounce=300').classes('w-72')
        page_info = ui.label('Page 1 of 1').classes('text-sm text-slate-500 ml-auto')
        prev_button = ui.button('Prev').classes('bg-slate-200 text-slate-700')
        next_button = ui.button('Next').classes('bg-slate-200 text-slate-700')

    columns = [
        {'name': 'title', 'label': 'Title', 'field': 'title', 'sortable': True},
        {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True},
        {'name': 'start_date', 'label': 'Start Date', 'field': 'start_date', 'sortable': True},
        {'name': 'last_updated', 'label': 'Last Updated', 'field': 'last_updated', 'sortable': True},
    ]

    table = (
        ui.table(columns=columns, rows=[], row_key='row_id')
        .classes('w-full text-sm q-table--striped')
        .props('flat wrap-cells square separator="horizontal"')
    )

    @table.add_slot('body-cell-status')
    def _(row: Dict[str, Any]) -> None:
        label = row.get('status') or '--'
        normalized = label.lower()
        style = 'bg-slate-100 text-slate-700'
        for key, val in STATUS_STYLES.items():
            if key in normalized:
                style = val
                break
        ui.label(label or '--').classes(f'{style} px-2 py-1 rounded text-xs font-semibold uppercase')

    def set_loading(is_loading: bool) -> None:
        spinner.style('display: inline-block;' if is_loading else 'display: none;')
        refresh_button.set_enabled(not is_loading)
        sync_button.set_enabled(not is_loading)

    def update_table_rows(rows: List[Dict[str, Any]]) -> None:
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

    def apply_filters() -> None:
        search_term = state['search'].lower()
        filtered = []
        for row in state['rows']:
            haystack = f"{row.get('title', '')} {row.get('status', '')}".lower()
            if search_term and search_term not in haystack:
                continue
            filtered.append(row)

        state['filtered'] = filtered
        total_pages = max(1, math.ceil(len(filtered) / ROWS_PER_PAGE)) if filtered else 1
        if state['page'] >= total_pages:
            state['page'] = total_pages - 1

        start = state['page'] * ROWS_PER_PAGE
        end = start + ROWS_PER_PAGE
        current_slice = filtered[start:end]
        update_table_rows(current_slice)

        page_info.text = f"Page {state['page'] + 1} of {total_pages} ({len(filtered)} rows)"

    async def fetch_data(show_toast: bool = False, auto_trigger: bool = False) -> None:
        set_loading(True)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_url("/api/productions/fetch"))
            response.raise_for_status()
            payload = response.json()
            if payload.get('status') != 'success':
                raise ValueError(payload.get('message', 'Unable to fetch productions'))
            raw_rows = payload.get('data', [])
            state['rows'] = [_decorate_row(row) for row in raw_rows]
            state['page'] = 0
            apply_filters()
            message = payload.get('message', f'Loaded {len(state["rows"])} productions')
            if payload.get('source') == 'cache':
                message += ' (from cache)'
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status_label.text = f"{message} @ {timestamp}"
            status_label.classes('text-sm text-slate-500')
            if show_toast and not auto_trigger:
                ui.notify(message, type='positive')
        except Exception as exc:  # noqa: BLE001
            status_label.text = f'Error: {exc}'
            status_label.classes('text-sm text-red-600')
            ui.notify(f'Failed to load productions: {exc}', type='negative')
        finally:
            set_loading(False)

    async def sync_now() -> None:
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
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url("/api/productions/sync"),
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()
            if data.get('status') != 'success':
                raise ValueError(data.get('message', 'Sync failed'))
            ui.notify(data.get('message', 'Sync completed'), type='positive')
            await fetch_data()
        except Exception as exc:  # noqa: BLE001
            status_label.text = f'Sync failed: {exc}'
            status_label.classes('text-sm text-red-600')
            ui.notify(f'Sync failed: {exc}', type='negative')
        finally:
            set_loading(False)

    def _decorate_row(row: Dict[str, Any]) -> Dict[str, Any]:
        start_iso = row.get('start_date')
        last_iso = row.get('last_updated')
        return {
            **row,
            'start_date_display': _format_local_date(start_iso),
            'last_updated_display': _format_local_timestamp(last_iso),
        }

    def on_search(event) -> None:
        state['search'] = (event.value or '').strip()
        state['page'] = 0
        apply_filters()

    def go_prev() -> None:
        if state['page'] > 0:
            state['page'] -= 1
            apply_filters()

    def go_next() -> None:
        total_pages = max(1, math.ceil(len(state['filtered']) / ROWS_PER_PAGE)) if state['filtered'] else 1
        if state['page'] < total_pages - 1:
            state['page'] += 1
            apply_filters()

    refresh_button.on('click', lambda _: ui.run_task(fetch_data(show_toast=True)))
    sync_button.on('click', lambda _: ui.run_task(sync_now()))
    search_input.on('update:model-value', on_search)
    prev_button.on('click', lambda _: go_prev())
    next_button.on('click', lambda _: go_next())
    auto_switch.on('update:model-value', lambda e: state.__setitem__('auto_refresh', bool(e.value)))

    async def auto_refresh_task() -> None:
        if state['auto_refresh']:
            await fetch_data(auto_trigger=True)

    ui.timer(AUTO_REFRESH_SECONDS, lambda: ui.run_task(auto_refresh_task()))

    ui.run_task(fetch_data())


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
