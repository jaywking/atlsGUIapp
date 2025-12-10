# ATLS GUI App - Above the Line Safety

A browser-based control surface for Above the Line Safety (ATLS) workflows.  
ATLSApp integrates production data, location data, medical facility lookups, and operational diagnostics into one unified interface.

Current Version: v0.9.4

Built with:

- NiceGUI (UI)
- FastAPI (API)
- Python services for Notion, Google Maps, background sync, and logging

This app modernizes your LocationSync and Medical Facility automation scripts into a reliable GUI with strong diagnostics and structured workflows.

---

## Release Notes (v0.9.4 highlights)

- Streaming Admin Tools expanded: Dedup Scan (`/api/locations/dedup_stream`), Diagnostics (`/api/locations/diagnostics_stream`), and System Info (`/api/system_info`) now use the same line-by-line streaming model as Match All, Schema Update, and Cache Management. Buttons disable during runs; outputs stream into read-only text areas.
- Dedup Scan detects duplicate Place_ID and canonical address hashes across Locations Master and all production `_Locations` tables.
- Diagnostics streams master row counts, missing Place_ID counts, cache index sizes, and Notion/Maps credential presence.
- System Info returns structured app/runtime/cache/credential metadata.
- Compatible with canonical ingestion (v0.9.x). Production selector → reprocess mapping issues are tracked in Parking Lot.
- v0.9.2 – Admin Tools streaming: Match All, Schema Update, and Cache Management actions now stream real-time progress to the UI (line-by-line).
- v0.9.1 – Master Canonicalization & Matching Stability: Added master rebuild CLI to overwrite all Locations Master rows with canonical normalized fields (ATLS Full Address, ISO country, refreshed Place_ID/lat/lng/county/borough, formatted_address_google). Matching cache rebuilt with canonical indexes (place_id, address hash, city/state/zip) and deterministic priority. Schema verification helper patches all _Locations databases to canonical fields (including formatted_address_google). Matching now assumes canonical inputs only.
- v0.9.0 – Canonical Ingestion: Full Address triggers a fresh Google Places lookup; structured fields, Place_ID, lat/lng, county/borough, and formatted_address_google overwrite; ATLS Full Address enforced; ingestion rejects rows without Full Address or structured fields; canonical Notion payloads only.

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

## Address Repair Tool

What it does  
`scripts/repair_addresses.py` performs in-place normalization of address data across production location tables, Locations Master, and Medical Facilities. It aligns existing Notion rows to the canonical schema and corrects historical inconsistencies without recreating pages.

When to use it  
- After schema alignment, ingestion bugs, or migrations.  
- When Notion tables have inconsistent or partially filled address fields.  
- Corrective tool only; not part of routine ingestion.

Canonical fields  
- address1/2/3, city, state, zip, country  
- county, borough  
- Full Address, Place_ID  
- Latitude, Longitude

How to run  
- Interactive:  
  ```
  python -m scripts.repair_addresses
  ```
- Non-interactive example:  
  ```
  python -m scripts.repair_addresses --target productions --dry-run
  ```

Logging  
Patch operations are written to `logs/address_repair_patches.log`.

## Master Rebuild (v0.9.1)
- Use `python -m scripts.repair_master` to canonicalize all Locations Master rows with the ingestion normalizer (Google refresh, ATLS Full Address, ISO country, formatted_address_google, Place_ID/lat/lng, county/borough).
- Use `python -m scripts.verify_schema` to ensure all Locations Master and production `_Locations` tables have the canonical schema (address1/2/3, city, state, zip, country, county, borough, Full Address, formatted_address_google, Place_ID, Latitude, Longitude, Status).

## Migration Note (v0.9.1)

Legacy fallback address parsing remains removed. All ingestion paths require Full Address or structured fields; Full Address inputs always refresh via Google, overwrite structured data, and store formatted_address_google internally. Matching now uses only canonical indexes (Place_ID → address hash → city/state/zip).

## Migration Note (v0.9.0)

Legacy fallback address parsing is removed as of v0.9.0. All ingestion paths now require Full Address or structured fields, and Full Address inputs always refresh via Google with ATLS-formatted outputs (including formatted_address_google internally).

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
- The page centralizes Match All (streams progress), Schema Update (streams progress), Cache Management (streams progress), Normalization, Reprocess, Dedup admin, Diagnostics, and System Info tools.

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
