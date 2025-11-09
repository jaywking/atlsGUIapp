from nicegui import ui
import requests


def page_content():
    """Locations page for selected Production."""

    ui.label('Locations for: Sample Production').classes('text-xl font-semibold')

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------
    with ui.row().classes('gap-3 mb-4'):
        ui.input('Search').props('outlined dense').classes('w-64')

        # Create the Process button and spinner
        process_button = ui.button('Process Selected').classes('bg-blue-500 text-white')
        spinner = ui.spinner(size='lg').props('color=primary').style('display: none;')

        ui.button('Reprocess All', on_click=lambda: ui.notify('Would reprocess all locations'))
        ui.button('View Details', on_click=lambda: ui.notify('Would open detail drawer'))

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
    process_button.on('click', lambda: trigger_process(process_button, spinner))


# ----------------------------------------------------------------------
# Backend Trigger Function
# ----------------------------------------------------------------------

def trigger_process(button, spinner):
    """Call the FastAPI endpoint to run process_new_locations with a spinner."""
    button.set_enabled(False)
    spinner.style('display: inline-block; margin-left: 8px;')
    ui.notify('Processing locations...', type='info')

    try:
        response = requests.post("http://localhost:8080/api/locations/process", timeout=60)
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "info")
            message = data.get("message", "No response message")
            ui.notify(message, type=status)
        else:
            ui.notify(f"Error: {response.status_code}", type="negative")
    except Exception as e:
        ui.notify(f"Request failed: {e}", type="negative")
    finally:
        spinner.style('display: none;')
        button.set_enabled(True)
