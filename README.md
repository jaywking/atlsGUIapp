# ATLS GUI App - Above the Line Safety

A browser-based control surface for Above the Line Safety (ATLS) workflows.  
ATLSApp integrates production data, location data, medical facility lookups, and operational diagnostics into one unified interface.

Current Version: v0.8.11.7

Built with:

- NiceGUI (UI)
- FastAPI (API)
- Python services for Notion, Google Maps, background sync, and logging

This app modernizes your LocationSync and Medical Facility automation scripts into a reliable GUI with strong diagnostics and structured workflows.

---

## Release Notes (v0.8.x Highlights)

- v0.8.2 - Master Matching Logic: match production locations to Locations Master via Place_ID first, then hierarchical address fallback; set LocationsMasterID relations and Status=Matched when unique; logs matching outcomes; `/api/locations/match_all`.
- v0.8.1.2 - Status Enforcement: centralized status defaults for all location writes (Unresolved without Place_ID, Ready with Place_ID, Matched when linked); applies to import, backfill, and API helpers.
- v0.8.1.1 - Schema Update: on-demand admin endpoint to add structured address fields to all `_Locations` tables plus master/facilities DBs; Status option updates remain manual per Notion constraints.
- v0.8.1.0 - Batch Location Import: async import job per production with duplicate handling, cache refresh, and logging.
- v0.7.x - Hybrid caches, background jobs, structured address parsing, and server-side search for Locations/Facilities.

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
- Dark-mode toggle remains available (header, top right), but visuals are inconsistent and deferred for a later milestone.
- Consistent Material-style table styling across all pages with finalized header alignment.
- Multi-table theming is applied automatically via the global theme block.

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

- Windows users may start the app via `scripts/run_atlsapp.ps1` for a guided, standardized startup experience.

```
uvicorn app.main:fastapi_app --reload
```

---

## Documentation

- Project Framework: `docs/ATLSApp - Project Framework (v1.0).md`
- Handbook: `docs/PROJECT_HANDBOOK.md`
- Developer Notes: `docs/DEV_NOTES.md`
- Agent Model: `docs/AGENTS.md`

---

## Admin Access

- A dedicated Admin Tools page is available at `/admin_tools` when `DEBUG_ADMIN=true`.
- The page centralizes Match All, Schema Update, Cache Management, Normalization, Reprocess, Dedup admin, Diagnostics, and System Info tools.

---

## Version History (summary)

- v0.4.0 - Dashboard  
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
- v0.4.14 - Content Wrapper & Header Dark Mode Completion
- v0.4.14b - Header Dark Mode Override & Unified Page Header Blocks
- v0.4.15b - Unified Dark-Mode Alignment & Theme Persistence Fix
- v0.4.16 - Dark-Mode Stabilization
- v0.4.17 - Dark Mode Follow-up Needed
- v0.5.0 - Refactor Release (codebase cleaned and reorganized; UI modules standardized; API/services consolidated; no functional changes)
- v0.5.1 - UI Polish (header alignment, control spacing, table padding, hover/focus styling; no functional changes)
- v0.5.2 - Productions Search Fix (restored client-side search on /productions; case-insensitive filtering across core fields; no layout or backend changes)
- v0.7.x - Hybrid cache layer, background jobs, structured address parsing, server-side search
- v0.8.1.x - Structured address schema/backfill and status enforcement
- v0.8.2 - Master matching (Place_ID/address fallback) with relation updates and match_all endpoint


## Current Focus (v0.8.x)

- Continue matching/duplicates hardening (auto/manual review flows).
- Ensure Location creation paths always carry structured addresses and enforced Status defaults.
- Prepare deduplication and future UI hooks without altering schemas automatically (Status options remain manual when missing).


## Development Guardrails
See `docs/DEV_NOTES.md` for NiceGUI slot rules, async-only HTTP, and Codex 5.1 guardrails.
