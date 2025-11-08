from nicegui import ui

def page_content():
    ui.label('Facilities near selected location').classes('text-xl font-semibold')
    with ui.row().classes('gap-3'):
        ui.button('Refresh Facilities', on_click=lambda: ui.notify('Would fetch from Google / Notion'))
        ui.button('Backfill Details', on_click=lambda: ui.notify('Would backfill facility details'))

    rows = [
        {'Facility Name': 'Northside Urgent Care', 'Type': 'Urgent Care', 'Address': '500 Medical Dr', 'Phone': '(203) 555-0100', 'Hours': 'Mon-Fri 8-8'},
        {'Facility Name': 'St. Mary\'s ER', 'Type': 'Emergency', 'Address': '12 Hospital Way', 'Phone': '(203) 555-2211', 'Hours': '24/7'},
    ]

    ui.table(
        columns=[
            {'name': 'Facility Name', 'label': 'Facility Name', 'field': 'Facility Name'},
            {'name': 'Type', 'label': 'Type', 'field': 'Type'},
            {'name': 'Address', 'label': 'Address', 'field': 'Address'},
            {'name': 'Phone', 'label': 'Phone', 'field': 'Phone'},
            {'name': 'Hours', 'label': 'Hours', 'field': 'Hours'},
        ],
        rows=rows,
        row_key='Facility Name'
    ).classes('w-full')

    # placeholder map area
    ui.label('Map preview will go here').classes('text-slate-400 italic pt-4')
    ui.card().classes('w-full h-64 bg-slate-100 items-center justify-center flex'):
        ...