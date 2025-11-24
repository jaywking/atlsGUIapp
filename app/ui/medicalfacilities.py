import asyncio
import httpx
from nicegui import ui

from app.services.api_client import api_url

def page_content():
    """Medical Facilities page for selected Master Location."""

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------
    with ui.row().classes(
        "atls-page-header w-full items-center flex-wrap gap-3 mb-4 "
        "px-4 py-2.5 bg-white text-slate-900 "
        "dark:bg-slate-900 dark:text-slate-200 "
        "border-b border-slate-200 dark:border-slate-700"
    ):
        fetch_button = ui.button('Fetch Facilities').classes('bg-blue-500 text-white')
        spinner = ui.spinner(size='lg').props('color=primary').style('display: none;')

        ui.button('Backfill Details', on_click=lambda: ui.notify('Would backfill facility details'))
        ui.button('Open in Maps', on_click=lambda: ui.notify('Would open Google Maps'))

    # ------------------------------------------------------------------
    # Facilities Table (Placeholder Data)
    # ------------------------------------------------------------------
    rows = [
        {
            'Facility Name': 'Northside Urgent Care',
            'Type': 'Urgent Care',
            'Address': '500 Medical Dr',
            'Phone': '(203) 555-0100',
            'Hours': 'Mon-Fri 8-8',
        },
        {
            'Facility Name': "St. Mary's ER",
            'Type': 'Emergency',
            'Address': '12 Hospital Way',
            'Phone': '(203) 555-2211',
            'Hours': '24/7',
        },
    ]

    ui.label('Nearby Medical Facilities').classes('text-lg font-semibold')
    ui.table(
        columns=[
            {'name': 'Facility Name', 'label': 'Facility Name', 'field': 'Facility Name'},
            {'name': 'Type', 'label': 'Type', 'field': 'Type'},
            {'name': 'Address', 'label': 'Address', 'field': 'Address'},
            {'name': 'Phone', 'label': 'Phone', 'field': 'Phone'},
            {'name': 'Hours', 'label': 'Hours', 'field': 'Hours'},
        ],
        rows=rows,
        row_key='Facility Name',
    ).classes('w-full')

    # Placeholder map
    with ui.card().classes('w-full h-64 bg-slate-100 flex items-center justify-center mt-4'):
        ui.label('Map container')

    # Link the fetch button to backend trigger
    fetch_button.on('click', lambda _: asyncio.create_task(trigger_fetch(fetch_button, spinner)))


# ----------------------------------------------------------------------
# Backend Trigger Function
# ----------------------------------------------------------------------

async def trigger_fetch(button, spinner):
    """Call the FastAPI endpoint to run fetch_medical_facilities with a spinner."""
    button.set_enabled(False)
    spinner.style('display: inline-block; margin-left: 8px;')
    ui.notify('Fetching facilities...', type='info')

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(api_url("/api/facilities/fetch"))
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
