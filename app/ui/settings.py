import requests
from nicegui import ui

from app.services.api_client import api_url


def page_content():
    ui.label('Settings').classes('text-xl font-semibold')

    with ui.card().classes('w-full max-w-2xl mt-4'):
        ui.label('Connection Tests').classes('text-lg font-semibold')
        ui.label('Validate Notion and Google Maps credentials stored in the server environment.').classes('text-sm text-slate-500 mb-4')

        status_labels = {}
        for service, label in [('notion', 'Notion API'), ('maps', 'Google Maps')]:
            with ui.row().classes('items-center justify-between w-full mb-2'):
                ui.label(label).classes('font-medium')
                status_labels[service] = ui.label('Not tested').classes('text-slate-500 text-sm')

        summary_label = ui.label('No test run yet.').classes('text-sm text-slate-500 mt-2')
        spinner = ui.spinner(size='md').style('display: none;')

        def update_status(name: str, success: bool, message: str) -> None:
            label = status_labels[name]
            text = 'Connected' if success else message
            label.text = text
            label.classes.clear()
            label.classes('text-sm')
            label.classes('text-green-600 font-semibold' if success else 'text-red-600')

        def run_tests() -> None:
            spinner.style('display: inline-block; margin-top: 12px;')
            summary_label.text = 'Testing connections...'
            summary_label.classes.clear()
            summary_label.classes('text-sm text-slate-500')
            try:
                response = requests.post(api_url("/api/settings/test_connections"), timeout=20)
                response.raise_for_status()
                data = response.json()
            except Exception as exc:  # noqa: BLE001
                summary_label.text = f'Connection test failed: {exc}'
                summary_label.classes.clear()
                summary_label.classes('text-sm text-red-600')
                spinner.style('display: none;')
                for service in status_labels:
                    update_status(service, False, 'Request failed')
                return

            notion_success = data.get('notion') == 'Connected'
            maps_success = data.get('maps') == 'Connected'

            update_status('notion', notion_success, data.get('notion', 'Error'))
            update_status('maps', maps_success, data.get('maps', 'Error'))

            overall_success = notion_success and maps_success
            summary_label.text = data.get('message', 'Finished')
            summary_label.classes.clear()
            summary_label.classes('text-sm text-green-600' if overall_success else 'text-sm text-red-600')
            ui.notify(summary_label.text, type='positive' if overall_success else 'warning')
            spinner.style('display: none;')

        ui.button('Test Connections', on_click=run_tests).classes('bg-blue-500 text-white mt-4 w-48')
