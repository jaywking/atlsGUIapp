from fastapi import FastAPI
from nicegui import ui

from app.ui import layout
from app.ui import productions, locations, facilities, jobs, settings

fastapi_app = FastAPI(title='ATLSApp')

# Home / default route goes to productions
@ui.page('/')
def index_page():
    layout.shell('Productions', productions.page_content)

@ui.page('/productions')
def productions_page():
    layout.shell('Productions', productions.page_content)

@ui.page('/locations')
def locations_page():
    layout.shell('Locations', locations.page_content)

@ui.page('/facilities')
def facilities_page():
    layout.shell('Facilities', facilities.page_content)

@ui.page('/jobs')
def jobs_page():
    layout.shell('Jobs / Logs', jobs.page_content)

@ui.page('/settings')
def settings_page():
    layout.shell('Settings', settings.page_content)

ui.run_with(fastapi_app, host='0.0.0.0', port=8080)