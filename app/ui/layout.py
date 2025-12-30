from nicegui import ui

from app.services.api_client import api_url
from app.core.settings import settings

PAGE_HEADER_CLASSES = (
    "atls-page-header w-full items-center flex-wrap gap-3 mb-4 "
    "px-4 py-2.5 bg-white text-slate-900 "
    "dark:bg-slate-900 dark:text-slate-200 "
    "border-b border-slate-200 dark:border-slate-700"
)

SIDEBAR_LINKS = [
    ('Dashboard', '/', 'dashboard'),
    ('Productions', '/productions', 'folder'),
    ('Locations', '/locations', 'place'),
    ('Medical Facilities', '/facilities', 'medical_services'),
    ('RASP / Docs', '/productions', 'description'),  # placeholder
    ('Jobs / Logs', '/jobs', 'assignment'),
    ('Settings', '/settings', 'settings'),
]

DEBUG_ADMIN = settings.DEBUG_ADMIN


def shell(title: str, content_callable):
    dark_mode = ui.dark_mode()

    ui.add_head_html(
        """
<style>
/* ========================================================= */
/*  Section A - Base Global Styling & Typography             */
/* ========================================================= */
:root {
    font-family: Inter, Segoe UI, Arial, sans-serif;
    font-size: 15px;
}
/* Remove default max-width constraints so pages can span available width */
.nicegui-content,
.q-page,
.q-page-container,
.q-layout__section--main {
    max-width: none !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}
h1, h2, h3, h4 {
    letter-spacing: -0.2px;
    font-weight: 600;
}
.q-table thead th { font-weight: 600 !important; font-size: 14px !important; }
.q-table tbody td { font-size: 14px !important; }

/* ========================================================= */
/*  Section B - Light Mode Table & Layout Styles             */
/* ========================================================= */
.q-table thead th {
    background-color: #f2f2f2 !important;
    color: #333 !important;
    vertical-align: middle !important;
    padding: 6px 8px !important;
    white-space: nowrap !important;
    text-align: left !important;
    display: table-cell !important;
    border-color: #e2e8f0 !important;
}
.q-table tbody td {
    text-align: left !important;
    vertical-align: middle !important;
    padding: 6px 8px !important;
    white-space: nowrap !important;
    color: #111827 !important;
    border-bottom: 1px solid #e2e8f0 !important;
}

/* ========================================================= */
/*  Section C - Dark Mode Table & Layout Styles              */
/* ========================================================= */
.body--dark,
.body--dark .q-layout,
.body--dark .q-page,
.body--dark .q-page-container,
.body--dark .q-page-container > div,
.body--dark .nicegui-content,
.body--dark .q-page-sticky,
.body--dark .q-page-scroller {
    background-color: #020617 !important;
    color: #e5e7eb !important;
}
.body--dark .q-header,
.body--dark .q-header > div,
.body--dark .q-header .q-toolbar {
    background-color: #0f172a !important; /* slate-900 */
    color: #e5e7eb !important;            /* slate-200 */
    border-color: #334155 !important;     /* slate-700 */
}
.body--dark .q-drawer {
    background-color: #0f172a !important;
    color: #e5e7eb !important;
    border-right: 1px solid #1f2937 !important;
}
.body--dark .atls-page-header {
    background-color: #0f172a !important; /* slate-900 */
    color: #e5e7eb !important;            /* slate-200 */
    border-color: #334155 !important;     /* slate-700 */
}
.body--dark .atls-page-header * {
    color: inherit !important;
}
.body--dark .q-table thead th {
    background-color: #0f172a !important;
    color: #e5e7eb !important;
    border-color: #374151 !important;
    text-align: left !important;
}
.body--dark .q-table tbody td {
    background-color: #020617 !important;
    color: #e5e7eb !important;
    border-color: #374151 !important;
    text-align: left !important;
    border-bottom: 1px solid #4b5563 !important;
}

/* ========================================================= */
/*  Section D - Alignment Overrides (Final Authority)        */
/* ========================================================= */
.q-table thead th .q-table__th-content,
.q-table__th-content,
.q-table .q-table__th-content,
.q-table__td-content,
.q-table .q-table__td-content {
    justify-content: flex-start !important;
    align-items: center !important;
    text-align: left !important;
    width: 100% !important;
}
.q-table__th-content > span,
.q-table__th-content > div,
.q-table__td-content > span,
.q-table__td-content > div {
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
}
.q-table__th,
.q-table__td,
.q-table .q-table__th,
.q-table .q-table__td {
    text-align: left !important;
    justify-content: flex-start !important;
    align-items: center !important;
}
/* Final Quasar header alignment override - v0.4.13 */
.q-table thead th.text-right,
.q-table thead th.text-center {
    text-align: left !important;
    justify-content: flex-start !important;
}
.q-table thead th.sortable {
    position: relative !important;
    padding-right: 18px !important;
}
.q-table thead th.sortable .q-table__sort-icon,
.q-table thead th.sortable .q-table__sort-icon--right {
    position: absolute !important;
    right: 6px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    margin: 0 !important;
    float: none !important;
}
.body--dark .q-table thead th.text-right,
.body--dark .q-table thead th.text-center {
    text-align: left !important;
    justify-content: flex-start !important;
}
.body--dark .q-table thead th.sortable {
    position: relative !important;
    padding-right: 18px !important;
}
.body--dark .q-table thead th.sortable .q-table__sort-icon,
.body--dark .q-table thead th.sortable .q-table__sort-icon--right {
    position: absolute !important;
    right: 6px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    margin: 0 !important;
    float: none !important;
}

/* Ensure Global Header Bar respects dark mode */
.body--dark .atls-global-header {
    background-color: #0f172a !important;
    color: #f8fafc !important;              /* slate-50 */
    border-color: #334155 !important;
}

/* Header alignment */
.atls-header-tight {
    padding-left: 4px !important;
    padding-right: 4px !important;
}

</style>
"""
    )

    with ui.row().classes('w-full min-h-screen no-wrap items-start'):
        # sidebar
        with ui.column().classes('w-56 min-h-screen bg-slate-100 text-slate-900 gap-1.5 py-3 px-3 dark:bg-slate-800 dark:text-white'):
            ui.label('ATLSApp').classes('text-xl font-semibold pb-3 text-slate-900 dark:text-white')
            links = list(SIDEBAR_LINKS)
            if DEBUG_ADMIN:
                links.append(('Admin Tools', '/admin_tools', 'admin_panel_settings'))
            for text, link, icon in links:
                with ui.row().classes('items-center gap-2 w-full rounded px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-800'):
                    ui.icon(icon).classes('text-slate-700 dark:text-slate-100')
                    ui.link(text, link).classes('flex-1 text-slate-700 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white')
        # main area
        with ui.column().classes('flex-1 min-h-screen overflow-x-auto'):
            # header
            with ui.row().classes("atls-global-header w-full justify-between items-center px-1 py-4 bg-white text-slate-900 border-b border-slate-200 shadow-sm sticky top-0 z-10 dark:bg-slate-900 dark:text-white dark:border-slate-700"):
                ui.label(title).classes('text-2xl font-semibold text-slate-900 dark:text-white')
                with ui.row().classes('items-center gap-3'):
                    ui.label('DEV').classes('text-sm text-slate-500 dark:text-slate-200')
                    toggle_btn = ui.button(on_click=dark_mode.toggle).classes('px-4 py-1 rounded bg-slate-200 text-slate-900 hover:bg-slate-300 dark:bg-slate-700 dark:text-white dark:hover:bg-slate-600')
                    toggle_btn.bind_text_from(dark_mode, 'value', lambda v: "Switch to Light" if v else "Dark Mode")
            # page content
            with ui.column().classes(
                'flex-1 overflow-y-visible px-1 py-4 gap-4 '
                'bg-white text-slate-900 '
                'dark:bg-slate-900 dark:text-slate-200'
            ):
                with ui.element('div').classes('w-full max-w-none px-0'):
                    content_callable()
            api_url('/')  # prime API client base for background tasks
