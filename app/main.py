from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
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
# Initialize FastAPI with lifespan (startup/shutdown)
# ---------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(app: FastAPI):
    background_sync.ensure_started()
    yield


fastapi_app = FastAPI(title='ATLSApp', lifespan=_lifespan)
fastapi_app.mount("/static", StaticFiles(directory=_ROOT / "static"), name="static")

# UI page imports
from app.ui import admin_tools, dashboard, datatable1, dedup, jobs, layout, locations, location_detail, medicalfacilities, productions, production_detail, psl_detail, settings

# API router imports
import app.api.locations_api as locations_api
from app.api import (
    facilities_api,
    jobs_api,
    settings_api,
    dashboard_api,
    productions_api,
    medicalfacilities_api,
    notion_admin_api,
    psl_enrichment_api,
    schema_report_api,
)
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
fastapi_app.include_router(psl_enrichment_api.router)
fastapi_app.include_router(schema_report_api.router)


# ---------------------------------------------------------------------
# UI PAGES
# ---------------------------------------------------------------------

@ui.page('/', title='ATLS - Dashboard')
def index_page():
    layout.shell('Dashboard', dashboard.page_content)


@ui.page('/dashboard', title='ATLS - Dashboard')
def dashboard_page():
    layout.shell('Dashboard', dashboard.page_content)


@ui.page('/productions', title='ATLS - Productions')
def productions_page():
    layout.shell('Productions', productions.page_content)


@ui.page('/productions/{production_id}', title='ATLS - Production Details')
def production_detail_page(production_id: str):
    layout.shell('Production Details', lambda: production_detail.page_content(production_id))


@ui.page('/psl/{production_id}/{master_id}', title='ATLS - PSL Details')
def psl_detail_page(production_id: str, master_id: str):
    layout.shell('PSL Details', lambda: psl_detail.page_content(production_id, master_id))


@ui.page('/locations', title='ATLS - Locations')
def locations_page():
    layout.shell('Locations', locations.page_content)


@ui.page('/locations/{master_id}', title='ATLS - Location Details')
def location_detail_page(master_id: str):
    layout.shell('Location Details', lambda: location_detail.page_content(master_id))


@ui.page('/facilities', title='ATLS - Medical Facilities')
def facilities_page():
    layout.shell('Medical Facilities', medicalfacilities.page_content)


@ui.page('/jobs', title='ATLS - Jobs / Logs')
def jobs_page():
    layout.shell('Jobs / Logs', jobs.page_content)


@ui.page('/settings', title='ATLS - Settings')
def settings_page():
    layout.shell('Settings', settings.page_content)


@ui.page('/tools/dedup', title='ATLS - Dedup')
def dedup_page():
    layout.shell('Locations Master - Dedup Resolution', dedup.page_content)


@ui.page('/admin_tools', title='ATLS - Admin Tools')
async def admin_tools_page(request: Request):
    layout.shell('Admin Tools', lambda: admin_tools.page_content(request))

@ui.page('/datatable1', title='ATLS - DataTable1')
def datatable1_page():
    layout.shell('DataTable1', datatable1.page_content)


# ---------------------------------------------------------------------
# Run App
# ---------------------------------------------------------------------
ui.run_with(
    fastapi_app,
    reconnect_timeout=30.0,  # allow longer reconnect window for local socket stability
    message_history_length=5000,
    storage_secret="atlsapp-storage",
)

if __name__ == '__main__':
    ui.run(host='0.0.0.0', port=8080)
