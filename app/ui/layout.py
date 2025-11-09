from nicegui import ui

SIDEBAR_LINKS = [
    ('Dashboard', '/', 'dashboard'),
    ('Productions', '/productions', 'folder'),
    ('Locations', '/locations', 'place'),
    ('Facilities', '/facilities', 'medical_services'),
    ('RASP / Docs', '/productions', 'description'),  # placeholder
    ('Jobs / Logs', '/jobs', 'assignment'),
    ('Settings', '/settings', 'settings'),
]

def shell(title: str, content_callable):
    with ui.row().classes('w-full h-screen'):
        # sidebar
        with ui.column().classes('w-56 h-full bg-slate-100 gap-1 py-4 px-3'):
            ui.label('ATLSApp').classes('text-xl font-semibold pb-4')
            for text, link, icon in SIDEBAR_LINKS:
                with ui.row().classes('items-center gap-2'):
                    ui.icon(icon).classes('text-slate-700')
                    ui.link(text, link).classes('text-slate-800 hover:underline')
        # main area
        with ui.column().classes('flex-1 h-full'):
            # header
            with ui.row().classes('w-full items-center justify-between px-6 py-4 bg-white border-b'):
                ui.label(title).classes('text-2xl font-semibold')
                with ui.row().classes('items-center gap-3'):
                    ui.label('DEV').classes('text-sm text-slate-500')
                    ui.avatar('JA').classes('bg-blue-500 text-white')
            # page content
            with ui.column().classes('flex-1 overflow-y-auto px-6 py-4 gap-4'):
                content_callable()
