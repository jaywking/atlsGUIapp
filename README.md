# ATLS GUI App – Above the Line Safety

A browser-based control surface for Above the Line Safety (ATLS) workflows.  
ATLSApp integrates production data, location data, medical facility lookups, and operational diagnostics into one unified interface.

Built with:

- NiceGUI (UI)
- FastAPI (API)
- Python services for Notion, Google Maps, background sync, and logging

This app modernizes your LocationSync and Medical Facility automation scripts into a reliable GUI with strong diagnostics and structured workflows.

---

## Features (v0.4.13)

### Dashboard
- Enhanced per-service diagnostic timings (v0.4.5)
- Local-time normalization improvements
- More resilient async loaders and error states

### Productions
- Table layout supports horizontal scroll alongside the sidebar
- All headers/cells left-aligned for readability
- Locations Table condensed to a clickable “Link”
- ProductionID opens the corresponding Notion page (NotionURL mapped automatically)
- Browser fetch reliability, logging, and 8-second timeout enforcement remain in place
### UI Layout / v0.4.x Enhancements
- Improved global layout: fixed sidebar wrapping issues, added sticky headers, better overflow behavior, and stabilized main content width.
### UI/UX Features
- Global Light/Dark theme toggle (header, top right)
- Consistent Material-style table styling across all pages (light + dark variants) with finalized header alignment
- Multi-table theming is applied automatically via the global theme block
- Full dark-mode coverage with reactive header/sidebar/toggle and persistent theme selection

### Settings
- Async diagnostics with refined timing metrics
- Slot-safe UI updates and consistent spinners

### Jobs
- Expanded logging visibility and fetch lifecycle entries
- Highlighting, filtering, and improved archive operations

### Locations & Medical Facilities
- Backend logic matured (async conversion, diagnostics, logging)
- UI placeholders now backed by functional service endpoints

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
- v0.4.5 – Async Diagnostics Timing  
- v0.4.6 – Full Async Conversion  
- v0.4.7 - Productions Table UX, Slot Fixes, Page-Context Enforcement
- v0.4.8 - Productions Layout & UX Improvements
- v0.4.9 - Productions Notion Link Integration
- v0.4.10 - Global Layout Improvements
- v0.4.11 - Global Theme + Material Table Styles
- v0.4.12 - Final Table Header Alignment & CSS Consolidation
- v0.4.13 - Dark Mode Polish, Persistent Theme, Typography


## Next Steps (v0.4.14 planning)

- Extend Locations & Medical Facilities full UI
- Add cache rotation utilities
- Add dashboard UI configuration options
- Introduce error-handling standards across API/UI/services
- Improve documentation governance and consolidate DEV_NOTES variants


## Development Guardrails
See `docs/DEV_NOTES.md` for NiceGUI slot rules, async-only HTTP, and Codex 5.1 guardrails.
