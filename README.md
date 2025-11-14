# ATLS GUI App – Above the Line Safety

A browser-based control surface for Above the Line Safety (ATLS) workflows.  
ATLSApp integrates production data, location data, medical facility lookups, and operational diagnostics into one unified interface.

Built with:

- NiceGUI (UI)
- FastAPI (API)
- Python services for Notion, Google Maps, background sync, and logging

This app modernizes your LocationSync and Medical Facility automation scripts into a reliable GUI with strong diagnostics and structured workflows.

---

## Features (v0.4.4)

### Dashboard

- Notion (Locations + Productions) connection status  
- Google Maps API health  
- Total productions and total locations  
- Recent jobs (24h), shown in local time  
- Spinners and a consistent card layout for async loads

### Productions

- Live Notion-backed table  
- Search and pagination  
- Alternating row colors  
- Colored status chips  
- Manual Refresh and Sync  
- Auto-refresh toggle  
- Background sync with cache fallback  
- Sync status surfaced in Settings

### Settings

- Fully async “Test Connections”  
- Parallelized checks (Notion Locations, Notion Productions, Google Maps)  
- Per-service results  
- Sync interval and cache path display  
- “Run Auto Sync Now” button  

### Jobs

- Full JSONL log table  
- Category and status filters  
- Free-text search  
- Highlighting of newest entries  
- Manual archive (log pruning)

### Locations & Medical Facilities

- Placeholder UIs ready for expansion

---

## Folder Structure

```
atlsGUIapp/
├─ app/
│  ├─ main.py
│  ├─ ui/
│  ├─ api/
│  ├─ services/
│  ├─ data/
│  └─ services/logging_setup.py
├─ scripts/
├─ docs/
├─ .env
└─ requirements.txt
```

---

## Technology Overview

- **Frontend:** NiceGUI  
- **Backend:** FastAPI  
- **Architecture:** Async-first (httpx + asyncio)  
- **External Services:** Notion REST API, Google Maps Places/Geocode  
- **Storage:**  
  - JSONL log with rotation and archive  
  - Production cache for offline read and improved resiliency

---

## Local Development

### Environment Setup

```
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### .env File (example)

```
NOTION_TOKEN=
NOTION_LOCATIONS_DB_ID=
NOTION_PRODUCTIONS_DB_ID=
GOOGLE_MAPS_API_KEY=
PRODUCTIONS_CACHE_PATH=app/data/cache/productions.json
LOG_PATH=app/data/jobs.log
PRODUCTIONS_SYNC_INTERVAL=900
```

### Run the App

```
uvicorn app.main:fastapi_app --reload
```

---

## Documentation

- Project Framework: `docs/ATLSApp – Project Framework (v1.0).md`
- Handbook: `docs/PROJECT_HANDBOOK.md`
- Developer Notes: `docs/DEV_NOTES.md`
- Agent Model: `docs/AGENTS.md`

---

## Version History (summary)

- v0.4.0 – Dashboard  
- v0.4.1 – Hardening & Env Autoload  
- v0.4.2 – Productions + Sync  
- v0.4.3 – UI Enhancements + Background Sync  
- v0.4.4 – Diagnostics UX Polish  

---

## Next Steps (v0.4.5 candidates)

- Convert synchronous UI actions to async  
- Add diagnostic timing metrics  
- Dashboard UI configuration options  
- Inline editing for productions  
- Cache rotation utilities  
- Locations & Medical Facilities feature expansion  

---

# © Above the Line Safety
Designed for internal use and continuous expansion within the ATLS ecosystem.
