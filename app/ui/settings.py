import httpx
from datetime import datetime, timezone
from nicegui import ui

from app.services.api_client import api_url
from app.services import background_sync


def page_content():
    with ui.row().classes(
        "atls-page-header w-full items-center flex-wrap gap-3 mb-4 "
        "px-4 py-2.5 bg-white text-slate-900 "
        "dark:bg-slate-900 dark:text-slate-200 "
        "border-b border-slate-200 dark:border-slate-700"
    ):
        ui.space()

    with ui.card().classes('w-full max-w-2xl mt-4'):
        ui.label('Connection Tests').classes('text-lg font-semibold')
        ui.label('Validate Notion and Google Maps credentials stored in the server environment.').classes('text-sm text-slate-500 mb-4')

        status_labels = {}
        time_labels = {}
        service_rows = [
            ('notion', 'Notion API (Locations DB)', 'notion_locations'),
            ('productions', 'Productions DB', 'notion_productions'),
            ('maps', 'Google Maps', 'google_maps'),
        ]
        for service, label, _ in service_rows:
            with ui.column().classes('w-full mb-2'):
                with ui.row().classes('items-center justify-between w-full'):
                    ui.label(label).classes('font-medium')
                    status_labels[service] = ui.label('Not tested').classes('text-slate-500 text-sm')
                time_labels[service] = ui.label('Time: —').classes('text-xs text-slate-500 ml-0')

        summary_label = ui.label('No test run yet.').classes('text-sm text-slate-500 mt-2')
        spinner = ui.spinner(size='md').style('display: none;')

        def update_status(name: str, success: bool, message: str) -> None:
            label = status_labels[name]
            text = 'Connected' if success else message
            label.text = text
            label.classes.clear()
            label.classes('text-sm')
            label.classes('text-green-600 font-semibold' if success else 'text-red-600')

        def update_time(name: str, seconds) -> None:
            label = time_labels[name]
            try:
                if seconds is None:
                    raise ValueError('missing')
                ms = int(float(seconds) * 1000)
                label.text = f'Time: {ms} ms'
            except (TypeError, ValueError):
                label.text = 'Time: —'

        async def run_tests() -> None:
            spinner.style('display: inline-block; margin-top: 12px;')
            summary_label.text = 'Testing connections...'
            summary_label.classes.clear()
            summary_label.classes('text-sm text-slate-500')
            try:
                async with httpx.AsyncClient(timeout=35.0) as client:
                    response = await client.post(api_url("/api/settings/test_connections"))
                    response.raise_for_status()
                    data = response.json()
            except Exception as exc:  # noqa: BLE001
                summary_label.text = f'Connection test failed: {exc}'
                summary_label.classes.clear()
                summary_label.classes('text-sm text-red-600')
                spinner.style('display: none;')
                for service in status_labels:
                    update_status(service, False, 'Request failed')
                    update_time(service, None)
                return

            notion_success = data.get('notion') == 'Connected'
            productions_success = data.get('productions') == 'Connected'
            maps_success = data.get('maps') == 'Connected'

            update_status('notion', notion_success, data.get('notion', 'Error'))
            update_status('productions', productions_success, data.get('productions', 'Error'))
            update_status('maps', maps_success, data.get('maps', 'Error'))

            timing_payload = data.get('timing') or {}
            for service, _, timing_key in service_rows:
                update_time(service, timing_payload.get(timing_key))

            overall_success = notion_success and maps_success and productions_success
            summary_label.text = data.get('message', 'Finished')
            summary_label.classes.clear()
            summary_label.classes('text-sm text-green-600' if overall_success else 'text-sm text-red-600')
            ui.notify(summary_label.text, type='positive' if overall_success else 'warning')
            spinner.style('display: none;')

        ui.button('Test Connections', on_click=run_tests).classes('bg-blue-500 text-white mt-4 w-48')

    with ui.card().classes('w-full max-w-2xl mt-4'):
        ui.label('Productions Auto Sync').classes('text-lg font-semibold')
        sync_info_label = ui.label('Loading sync status...').classes('text-sm text-slate-500')
        sync_status_label = ui.label('').classes('text-sm text-slate-500')
        sync_spinner = None  # type: ignore[assignment]
        auto_sync_button = None  # type: ignore[assignment]

        def format_sync_label(data: dict) -> str:
            interval = data.get('interval_minutes')
            cache_path = data.get('cache_path')
            enabled = data.get('auto_sync_enabled')
            return f"Interval: {interval} min | Cache: {cache_path} | Enabled: {enabled}"

        def format_sync_status(data: dict) -> str:
            ts = data.get('last_sync_timestamp') or data.get('cache_timestamp') or '--'
            if ts and ts != '--':
                ts = _format_local_timestamp(ts)
            count = data.get('record_count') or data.get('cache_record_count')
            return f"Last Sync: {ts} | Records: {count or 0} | Status: {data.get('last_status')}"

        def load_sync_status() -> None:
            try:
                payload = background_sync.get_status()
                sync_info_label.text = format_sync_label(payload)
                sync_status_label.text = format_sync_status(payload)
                sync_status_label.classes('text-sm text-slate-500')
            except Exception as exc:  # noqa: BLE001
                sync_info_label.text = f'Unable to load sync status: {exc}'
                sync_status_label.text = ''

        async def run_auto_sync() -> None:
            if sync_spinner:
                sync_spinner.style('display: inline-block;')
            if auto_sync_button:
                auto_sync_button.disable()
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        api_url("/api/productions/sync"),
                        json={'operation': 'auto_sync'},
                    )
                response.raise_for_status()
                data = response.json()
                if data.get('status') != 'success':
                    raise ValueError(data.get('message', 'Auto sync failed'))
                ui.notify(data.get('message', 'Auto sync complete'), type='positive')
                load_sync_status()
            except Exception as exc:  # noqa: BLE001
                ui.notify(f'Auto sync failed: {exc}', type='negative')
            finally:
                if auto_sync_button:
                    auto_sync_button.enable()
                if sync_spinner:
                    sync_spinner.style('display: none;')

        with ui.row().classes('items-center gap-3 mt-4'):
            auto_sync_button = ui.button('Run Auto Sync Now', on_click=run_auto_sync).classes('bg-emerald-600 text-white w-56')
            sync_spinner = ui.spinner(size='sm').style('display: none;')

        load_sync_status()


def _format_local_timestamp(raw: str) -> str:
    if not raw:
        return '--'
    try:
        dt = datetime.fromisoformat(str(raw).replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return raw
