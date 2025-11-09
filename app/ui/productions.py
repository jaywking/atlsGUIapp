from nicegui import ui


def page_content() -> None:
    ui.label('Productions Dashboard').classes('text-xl font-semibold')
    ui.label('View and manage production data.').classes('text-slate-500 mb-4')

    with ui.card().classes('w-full max-w-3xl shadow-sm border border-slate-200'):
        ui.label('Upcoming Features').classes('text-lg font-semibold mb-2')
        ui.label(
            'This space will show Notion-synced production tables, filters, and quick actions. '
            'Use the Jobs page to monitor automation progress while this view is under construction.'
        ).classes('text-sm text-slate-600')

        with ui.row().classes('gap-3 mt-4'):
            ui.button('Back to Home', on_click=lambda: ui.navigate.to('/')).classes('bg-slate-800 text-white')
            ui.button('View Jobs', on_click=lambda: ui.navigate.to('/jobs')).classes('bg-blue-500 text-white')
