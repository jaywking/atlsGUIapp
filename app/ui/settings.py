from nicegui import ui

def page_content():
    ui.label('Settings').classes('text-xl font-semibold')
    ui.input('Notion Token').props('type=password').classes('w-96')
    ui.input('Google Maps API Key').props('type=password').classes('w-96')
    ui.input('S3 Bucket').classes('w-96')
    ui.button('Test Connections', on_click=lambda: ui.notify('Would test external services')).classes('mt-2')