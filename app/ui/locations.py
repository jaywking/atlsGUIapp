import asyncio
import httpx
from nicegui import ui

from app.services.api_client import api_url
from app.ui.layout import PAGE_HEADER_CLASSES


def page_content() -> None:
    """Locations page for selected Production."""

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------
    with ui.row().classes(f"{PAGE_HEADER_CLASSES} min-h-[52px] items-center"):
        with ui.row().classes('items-center gap-2 flex-wrap'):
            ui.input('Search').props('outlined dense').classes('w-64')
            process_button = ui.button('Process Selected').classes('bg-blue-500 text-white hover:bg-slate-100 dark:hover:bg-slate-800')
            spinner = ui.spinner(size='lg').props('color=primary').style('display: none;')
            ui.button('Reprocess All', on_click=lambda: ui.notify('Would reprocess all locations')).classes('bg-slate-200 text-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800')
            ui.button('View Details', on_click=lambda: ui.notify('Would open detail drawer')).classes('bg-slate-200 text-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800')

    # ------------------------------------------------------------------
    # Locations Table (Placeholder Data)
    # ------------------------------------------------------------------
    rows = [
        {
            'ProdLocID': 'LOC-001',
            'Location Name': 'Warehouse Exterior',
            'Address': '123 Mill Rd, Pittsburgh, PA',
            'Status': 'Ready',
            'Linked Master': 'Mill Rd Warehouse',
        },
        {
            'ProdLocID': 'LOC-002',
            'Location Name': 'Office Interior',
            'Address': '41 Hill St, Newark, NJ',
            'Status': 'Matched',
            'Linked Master': '41 Hill St',
        },
    ]

    ui.label('Locations').classes('text-lg font-semibold')
    with ui.element('div').classes('w-full overflow-x-auto py-2'):
        ui.table(
            columns=[
                {'name': 'ProdLocID', 'label': 'ProdLocID', 'field': 'ProdLocID'},
                {'name': 'Location Name', 'label': 'Location Name', 'field': 'Location Name'},
                {'name': 'Address', 'label': 'Address', 'field': 'Address'},
                {'name': 'Status', 'label': 'Status', 'field': 'Status'},
                {'name': 'Linked Master', 'label': 'Linked Master', 'field': 'Linked Master'},
            ],
            rows=rows,
            row_key='ProdLocID',
        ).classes('w-full')

    # Link the process button to backend trigger
    process_button.on('click', lambda _: asyncio.create_task(trigger_process(process_button, spinner)))


# ----------------------------------------------------------------------
# Backend Trigger Function
# ----------------------------------------------------------------------

async def trigger_process(button, spinner):
    """Call the FastAPI endpoint to run process_new_locations with a spinner."""
    button.set_enabled(False)
    spinner.style('display: inline-block; margin-left: 8px;')
    ui.notify('Processing locations...', type='info')

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(api_url("/api/locations/process"))
        response.raise_for_status()
        data = response.json()
        status = data.get("status", "info")
        message = data.get("message", "No response message")
        if data.get('status') == 'error':
            ui.notify(message, type='negative')
        else:
            ui.notify(message, type=status)
    except Exception as e:  # noqa: BLE001
        ui.notify(f"Request failed: {e}", type="negative")
    finally:
        spinner.style('display: none;')
        button.set_enabled(True)
