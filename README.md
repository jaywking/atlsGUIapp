
## 🔗 Future API & Logic Integration

The current version of **ATLS GUI App** provides layout-only pages for interface design and navigation.  
Backend logic will connect through **FastAPI** endpoints located in the `/app/api/` directory.

### Planned Connections

| UI Page | Planned Backend Logic | Description |
|----------|----------------------|--------------|
| **Productions** | Notion API (`sync_productions`) | Pull production lists and details directly from Notion’s *Productions Master* database. |
| **Locations** | `process_new_locations.py` | Process “Ready” locations, geocode via Google Maps, and sync updates to Notion. |
| **Medical Facilities** | `fetch_medical_facilities.py` | Find and refresh nearby medical facilities for each master location. |
| **Jobs / Logs** | Local CSV or Redis worker | Display recent task history, durations, and statuses. |
| **Settings** | `.env` configuration tester | Verify Notion, Google Maps, and S3 credentials from the config file. |

---

### Implementation Plan

Each backend feature will be exposed as a **FastAPI route**.  
Example:

app/api/locations_api.py

from fastapi import APIRouter

router = APIRouter()

@router.post(”/process_locations”)
def process_locations():
# TODO: integrate with scripts/process_new_locations.py
return {“status”: “ok”, “message”: “Locations processed (placeholder)”}

This route is then registered inside `app/main.py`:

from app.api import locations_api
fastapi_app.include_router(locations_api.router)

The frontend (NiceGUI) calls these routes using lightweight Python or JavaScript hooks to trigger scripts or refresh UI components.  
As each feature is connected, the GUI will evolve from a static layout into a fully functional operations console for production safety workflows.

---

### Next Steps

1. Add `/app/api/` folder with placeholder API files (starting with `locations_api.py`).  
2. Commit these changes to GitHub.  
3. When a desktop environment is available, connect real script logic and test the first endpoint.  

---