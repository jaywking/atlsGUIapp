from fastapi import FastAPI
from nicegui import ui

from app.ui import layout, productions, locations, medicalfacilities, jobs, settings
from app.api import locations_api   # ← add this line

fastapi_app = FastAPI(title='ATLSApp')

# register API routers
fastapi_app.include_router(locations_api.router)   # ← add this line

# UI pages
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
    layout.shell('Facilities', medicalfacilities.page_content)

@ui.page('/jobs')
def jobs_page():
    layout.shell('Jobs / Logs', jobs.page_content)

@ui.page('/settings')
def settings_page():
    layout.shell('Settings', settings.page_content)

ui.run_with(fastapi_app, host='0.0.0.0', port=8080)