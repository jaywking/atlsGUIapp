from nicegui import ui

def page_content():
    ui.label('Jobs / Logs').classes('text-xl font-semibold')
    rows = [
        {'Job ID': 'JOB-001', 'Task': 'Fetch Facilities', 'Status': 'Success', 'Started': '2025-10-28 10:10', 'Duration': '4.2s'},
        {'Job ID': 'JOB-002', 'Task': 'Process Locations', 'Status': 'Running', 'Started': '2025-10-28 10:12', 'Duration': '1.1s'},
    ]
    ui.table(
        columns=[
            {'name': 'Job ID', 'label': 'Job ID', 'field': 'Job ID'},
            {'name': 'Task', 'label': 'Task', 'field': 'Task'},
            {'name': 'Status', 'label': 'Status', 'field': 'Status'},
            {'name': 'Started', 'label': 'Started', 'field': 'Started'},
            {'name': 'Duration', 'label': 'Duration', 'field': 'Duration'},
        ],
        rows=rows,
        row_key='Job ID'
    ).classes('w-full')

    ui.label('Log output will display here once we wire to real jobs.').classes('text-slate-400 pt-3')