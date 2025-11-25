from fastapi import FastAPI
from nicegui import ui
from pathlib import Path
from dotenv import load_dotenv

from app.services.logging_setup import configure_logging

configure_logging()

# ---------------------------------------------------------------------
# Load environment from .env (repo root)
# ---------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[1]
_ENV = _ROOT / ".env"
load_dotenv(dotenv_path=_ENV if _ENV.exists() else None)

# ---------------------------------------------------------------------
# Initialize FastAPI
# ---------------------------------------------------------------------
fastapi_app = FastAPI(title='ATLSApp')

# UI page imports
from app.ui import layout, productions, locations, medicalfacilities, jobs, settings, dashboard

# API router imports
from app.api import locations_api, facilities_api, jobs_api, settings_api, dashboard_api, productions_api, medicalfacilities_api, notion_admin_api
from app.services import background_sync

# ---------------------------------------------------------------------
# Register API Routers
# ---------------------------------------------------------------------
fastapi_app.include_router(locations_api.router)
fastapi_app.include_router(facilities_api.router)
fastapi_app.include_router(medicalfacilities_api.router)
fastapi_app.include_router(jobs_api.router)
fastapi_app.include_router(settings_api.router)
fastapi_app.include_router(dashboard_api.router)
fastapi_app.include_router(productions_api.router)
fastapi_app.include_router(notion_admin_api.router)


@fastapi_app.on_event("startup")
async def _start_background_sync() -> None:
    background_sync.ensure_started()


# ---------------------------------------------------------------------
# UI PAGES
# ---------------------------------------------------------------------

@ui.page('/')
def index_page():
    layout.shell('Dashboard', dashboard.page_content)


@ui.page('/dashboard')
def dashboard_page():
    layout.shell('Dashboard', dashboard.page_content)


@ui.page('/productions')
def productions_page():
    layout.shell('Productions', productions.page_content)


@ui.page('/locations')
def locations_page():
    layout.shell('Locations', locations.page_content)


@ui.page('/facilities')
def facilities_page():
    layout.shell('Medical Facilities', medicalfacilities.page_content)


@ui.page('/jobs')
def jobs_page():
    layout.shell('Jobs / Logs', jobs.page_content)


@ui.page('/settings')
def settings_page():
    layout.shell('Settings', settings.page_content)


# ---------------------------------------------------------------------
# Run App
# ---------------------------------------------------------------------
ui.run_with(fastapi_app)

if __name__ == '__main__':
    ui.run(host='0.0.0.0', port=8080)
