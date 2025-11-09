from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from nicegui import ui

from app.services.api_client import api_url
TABLE_DOM_ID = "jobs-log-table"
HIGHLIGHT_COUNT = 5


def fetch_logs() -> List[Dict[str, Any]]:
    """Fetch job logs from the backend and validate the payload."""

    response = requests.get(api_url("/api/jobs/logs"), timeout=15)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "success":
        raise ValueError(data.get("message", "Failed to fetch logs"))
    logs = data.get("logs", [])
    if not isinstance(logs, list):
        raise ValueError("Malformed logs payload")
    return logs


def page_content() -> None:
    ui.label('Job History').classes('text-xl font-semibold')

    state: Dict[str, Any] = {
        "auto_refresh": False,
        "logs": [],
        "category": "all",
        "status": "all",
        "search": "",
    }

    with ui.row().classes('items-center gap-3 mb-3 w-full'):
        refresh_button = ui.button('Refresh').classes('bg-blue-500 text-white px-4')
        ui.switch('Auto-refresh (10s)').bind_value(state, 'auto_refresh')
        spinner = ui.spinner(size='md').props('color=primary').style('display: none;')
        last_updated = ui.label('Last updated: --').classes('text-sm text-slate-500 ml-auto')

    with ui.row().classes('gap-3 items-end w-full mb-2 flex-wrap'):
        category_select = ui.select(['all'], value='all', label='Category').classes('w-52')
        status_select = ui.select(['all', 'success', 'error'], value='all', label='Status').classes('w-52')
        search_input = ui.input(label='Search message...').props('clearable dense debounce=300').classes('w-64')
        result_count = ui.label('0 logs shown').classes('text-sm text-slate-500 mt-3')

    with ui.row().classes('items-center gap-3 mt-2'):
        archive_button = ui.button('Archive Now').classes('bg-slate-800 text-white')
        archive_spinner = ui.spinner(size='sm').style('display: none;')
        archive_summary = ui.label('No archive run yet.').classes('text-sm text-slate-500')

    columns = [
        {'name': 'timestamp', 'label': 'Timestamp', 'field': 'timestamp', 'sortable': True},
        {'name': 'category', 'label': 'Category', 'field': 'category', 'sortable': True},
        {'name': 'action', 'label': 'Action', 'field': 'action', 'sortable': True},
        {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True},
        {'name': 'message', 'label': 'Message', 'field': 'message'},
    ]

    table = (
        ui.table(columns=columns, rows=[], row_key='row_id')
        .classes('w-full text-sm')
        .props(f'id={TABLE_DOM_ID} wrap-cells flat density="comfortable" sort-by="timestamp" sort-order="desc"')
    )

    @table.add_slot('body-cell-status')
    def _(row: Dict[str, Any]) -> None:
        status_value = row.get('status', 'unknown')
        is_success = status_value == 'success'
        color_cls = 'bg-green-100 text-green-700' if is_success else 'bg-red-100 text-red-700'
        label = status_value.capitalize() if status_value else '-'
        ui.label(label).classes(f'{color_cls} px-2 py-1 rounded text-xs font-semibold uppercase')

    @table.add_slot('body-cell-message')
    def _(row: Dict[str, Any]) -> None:
        classes = 'px-2 py-1 rounded block'
        if row.get('recent'):
            classes += ' bg-slate-50'
        ui.label(row.get('message', '') or '-').classes(classes)

    def set_loading(is_loading: bool) -> None:
        refresh_button.set_enabled(not is_loading)
        spinner.style('display: inline-block;' if is_loading else 'display: none;')

    def update_category_options() -> None:
        categories = sorted({entry.get('category', '-') for entry in state['logs'] if entry.get('category')})
        options = ['all'] + categories if categories else ['all']
        category_select.options = options
        if state['category'] not in options:
            state['category'] = 'all'
            category_select.value = 'all'

    def apply_filters(auto_scroll: bool = False) -> None:
        rows = []
        search_lower = state['search'].lower()
        filtered: List[Dict[str, Any]] = []
        for entry in sorted(state['logs'], key=_timestamp_key, reverse=True):
            if state['category'] != 'all' and entry.get('category') != state['category']:
                continue
            if state['status'] != 'all' and (entry.get('status') or '').lower() != state['status']:
                continue
            combined = f"{entry.get('message', '')} {entry.get('action', '')}".lower()
            if search_lower and search_lower not in combined:
                continue
            filtered.append(entry)

        for idx, entry in enumerate(filtered):
            rows.append(
                {
                    "row_id": f"{entry.get('timestamp', 'unknown')}-{idx}",
                    "timestamp": entry.get('timestamp', '-'),
                    "category": entry.get('category', '-'),
                    "action": entry.get('action', '-'),
                    "status": (entry.get('status') or 'unknown').lower(),
                    "message": entry.get('message', ''),
                    "recent": idx < HIGHLIGHT_COUNT,
                }
            )

        table.rows = rows
        result_count.text = f"{len(rows)} log{'s' if len(rows) != 1 else ''} shown"

        if auto_scroll and rows:
            _scroll_to_latest()

    def load_logs(show_toast: bool = False, auto_scroll: bool = True) -> None:
        set_loading(True)
        try:
            state['logs'] = fetch_logs()
            update_category_options()
            apply_filters(auto_scroll=auto_scroll)
            last_updated.text = f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            if show_toast:
                ui.notify('Logs refreshed', type='positive')
        except Exception as exc:  # noqa: BLE001
            ui.notify(f'Unable to fetch logs: {exc}', type='negative')
        finally:
            set_loading(False)

    def run_archive() -> None:
        archive_button.set_enabled(False)
        archive_spinner.style('display: inline-block;')
        archive_summary.classes('text-sm text-slate-500')
        try:
            response = requests.post(api_url("/api/jobs/prune"), timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('status') != 'success':
                raise ValueError(data.get('message', 'Archive failed'))
            stats = data.get('stats', {})
            archive_summary.text = f"Kept {stats.get('kept', 0)}  |  Archived {stats.get('archived', 0)}"
            ui.notify('Logs archived', type='positive')
            load_logs(auto_scroll=True)
        except Exception as exc:  # noqa: BLE001
            archive_summary.text = f'Archive failed: {exc}'
            archive_summary.classes('text-sm text-red-600')
            ui.notify(f'Archive failed: {exc}', type='negative')
        finally:
            archive_spinner.style('display: none;')
            archive_button.set_enabled(True)

    def on_category_change(value: Optional[str]) -> None:
        state['category'] = value or 'all'
        apply_filters()

    def on_status_change(value: Optional[str]) -> None:
        state['status'] = value or 'all'
        apply_filters()

    def on_search_change(value: Optional[str]) -> None:
        state['search'] = (value or '').strip()
        apply_filters()

    category_select.on('update:model-value', lambda e: on_category_change(e.value))
    status_select.on('update:model-value', lambda e: on_status_change(e.value))
    search_input.on('update:model-value', lambda e: on_search_change(e.value))

    refresh_button.on('click', lambda: load_logs(show_toast=True, auto_scroll=True))
    archive_button.on('click', run_archive)
    ui.timer(10.0, lambda: load_logs(auto_scroll=True) if state.get('auto_refresh') else None)

    load_logs(auto_scroll=True)


def _timestamp_key(entry: Dict[str, Any]) -> datetime:
    ts = entry.get('timestamp')
    if not ts:
        return datetime.min
    trimmed = ts.rstrip('Z')
    try:
        return datetime.fromisoformat(trimmed)
    except ValueError:
        return datetime.min


def _scroll_to_latest() -> None:
    ui.run_javascript(
        f"""
        const tbl = document.getElementById('{TABLE_DOM_ID}');
        const body = tbl?.querySelector('.q-table__middle tbody');
        body?.lastElementChild?.scrollIntoView({{behavior: 'smooth', block: 'end'}});
        """
    )
