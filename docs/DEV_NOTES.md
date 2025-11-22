Refer to README.md and PROJECT_HANDBOOK.md for architecture and workflow rules.



# Source: DEV_NOTES_COMPLETE.md

# DEV_TOOLS.md – ATLSApp Developer Tools & Guardrails

## Purpose

Authoritative reference for Codex 5.1 rules, NiceGUI guardrails, and the human workflows we follow when building ATLSApp.

## Codex 5.1 Rules (Quick Recall)

* Async-only HTTP in UI code (`httpx.AsyncClient`); browser fetch via `ui.run_javascript` (8s timeout wrapper).
* All UI mutations must execute in a valid NiceGUI page slot/context.
* Table slots: use context-managed slots or column `body` lambdas; avoid decorator-style `@table.add_slot` in NiceGUI 3.2.x.
* API paths must stay relative (`/api/...`) and should be built via `app.services.api_client`.
* Every change requires a `docs/DEV_NOTES.md` session entry (date, session, milestone, summary, changes, testing, notes).
* `python -m compileall <files>` must pass for touched modules before commit.
* Preserve imports/helpers/logging; do not remove behavior or env handling unless explicitly requested.

## Human Developer Workflows

### Core Tools

* VS Code with ChatGPT (Genie AI + Codex 5.1 extensions).
* `uvicorn app.main:fastapi_app --reload` for live server.
* Python venv for isolation; `.env` at repo root for Notion/Maps credentials.
* Logging: `logs/app.log`, JSONL jobs (`app/data/jobs.log`), feature logs (e.g., `logs/productions.log`).

### Required Checks Before Commit

1. `python -m compileall app`
2. Manual smoke: `/dashboard`, `/productions`, `/settings`, `/jobs`
3. Confirm background sync starts (console/logs show interval loop)
4. Update `docs/DEV_NOTES.md`

## NiceGUI Guardrails

* Never mutate DOM outside the page slot; timers/tasks must route through page context.
* After setting `table.rows`, call `table.update()` so changes propagate.
* Avoid decorator-style slots; use `with table.add_slot(...)` or column `body` lambdas.
* Keep browser JS snippets minimal (no leading newlines); prefer shared constants and the 8s timeout wrapper.
* Do not rely on `ui.get_client()` in async tasks; prefer server-side calls and relative URLs.
* In NiceGUI 3.2.x, `add_slot` is a context manager (or template string), not a callable; define slot content inside `with table.add_slot('body-cell-...'):` and bind loop variables via default args. Do not put Python callables in `columns` (functions are not JSON-serializable at render time).

### Common Pitfalls to Avoid
- If the table goes blank or throws slot TypeErrors, remove custom slots and confirm the default table renders, then reintroduce slots one by one using the context-manager pattern above.

## API Development Rules

* Always return `{status, message, ...}`.
* Log jobs via `log_job()` on success and error.
* Maintain cache fallback behavior for Notion-backed endpoints.
* Handle missing credentials gracefully and surface clear user-facing messages.

## Sync & Background Tasks

* Background sync enabled via env (`PRODUCTIONS_SYNC_ENABLED`, interval minutes).
* Cache path: `app/data/productions_cache.json`; refresh after mapper/schema changes.
* When updating UI from timers/async helpers, ensure page context or server callbacks (avoid emit/JS bridges for state changes).

## Fetch Patterns

* Browser fetch for large datasets (e.g., productions) with 8s timeout + toast on failure.
* Server-side async for Notion updates/sync; never block the NiceGUI event loop.

## Logging & Diagnostics

* Use module loggers with actionable messages (operation, count, error).
* Ensure `logs/` exists before writing; keep severity aligned (INFO flow, WARNING/ERROR failures).
* Add feature-specific logs when debugging (e.g., `logs/productions.log`).

## Editable Tables (Productions Reference)

* Prefer server-side handlers in column `body` lambdas or context slots; avoid client `emit` bridges for edits.
* Dirty-row tracking must update the source list and `table.rows`, then call `table.update()`.
* Auto-refresh should pause when dirty rows exist and resume after sync/discard.

## Deployment / Ops Notes

* `.env` auto-loads in `app/main.py`; maintain `NOTION_*`, `GOOGLE_MAPS_API_KEY`, and sync envs.
* Relative API paths keep dev/staging/prod aligned (no host/port hard-coding).
* Review `docs/DEV_NOTES.md` frequently for current patterns and pitfalls.

---

# DEV_NOTES.md - ATLS GUI App

(Full reconstructed sessions 1–24.3 follow below.)

Date: 2025-11-09 18:59 -0500
Author: Codex 5 (Developer)
Milestone: v0.3 – Job Logging System

Summary

* Implemented lightweight job logger and integrated with API routes.
* Added `/api/jobs/logs` endpoint to expose logs to the UI.
* Updated API map documentation.

Changes

* Added `app/services/logger.py` providing `log_job()` and `read_logs()` using JSONL at `app/data/jobs.log`.
* Updated `app/api/locations_api.py` to log success/error for `/api/locations/process`.
* Updated `app/api/facilities_api.py` to log success/error for `/api/facilities/fetch`.
* Added `app/api/jobs_api.py` with `GET /api/jobs/logs` returning `{status, message, logs}`.
* Fixed router registration order and included Jobs router in `app/main.py`.

Testing

* Module import sanity: ensured API modules import and logger reads/writes without raising exceptions locally.
* Endpoints return JSON with `status` and `message`.

Notes

* UI page `app/ui/jobs.py` currently static.

---

Date: 2025-11-09 19:01 -0500 (Session 2)
Milestone: v0.3.1 - Live Jobs Log UI

Summary

* Connected Jobs UI to logs endpoint.
* Added badges, toggles, refresh.

---

Date: 2025-11-09 19:01 -0500 (Session 3)
Milestone: v0.3.1 - Live Jobs Log UI (Docs sync)

Summary

* Standardized JSON responses.

---

Date: 2025-11-09 19:01 -0500 (Session 4)
Milestone: v0.3.1 - Stabilization

Summary

* Restored Config shim.
* Fixed bootstrap.

---

Date: 2025-11-09 19:01 -0500 (Session 5)
Milestone: v0.3.2 - Log Pruning & Rotation

Summary

* Added pruning + archive.

---

Date: 2025-11-09 19:01 -0500 (Session 6)
Milestone: v0.3.3 – Settings Connection Tests

Summary

* Added Notion + Maps diagnostics.

---

Date: 2025-11-09 19:01 -0500 (Session 7)
Milestone: v0.3.4 – Jobs UI Enhancements

Summary

* Filtering, archive, highlight.

---

Date: 2025-11-09 19:01 -0500 (Session 8)
Milestone: v0.3.4 – Hotfix

Summary

* Restored productions stub.

---

Date: 2025-11-09 15:01 -0500 (Session 8.1)
Milestone: v0.3.4.1 – Diagnostics Logging

Summary

* Added logs for settings tests.

---

Date: 2025-11-09 15:01 -0500 (Session 8.2)
Milestone: v0.3.4.2 – File-based Logging

Summary

* Added logs/app.log handler.

---

Date: 2025-11-09 15:01 -0500 (Session 8.3)
Milestone: v0.3.4.2 – API Path Standardization Fix

Summary

* Relative-path builder added.

---

Date: 2025-11-10 15:01 -0500 (Session 9)
Milestone: v0.4.0 – Dashboard Kickoff

Summary

* Dashboard page + `/api/dashboard/summary`.

---

Date: 2025-11-10 15:01 -0500 (Session 10)
Milestone: v0.4.1 – Dashboard Hardening & Env Autoload

Summary

* Fixed slot errors; timestamps local.

---

Date: 2025-11-09 15:01 -0500 (Session 11)
Milestone: v0.4.2 – Productions Data View & Sync

Summary

* Added `/productions` UI + fetch/sync.

---

Date: 2025-11-09 15:01 -0500 (Session 12)
Milestone: v0.4.3 – UI Enhancements & Background Sync

Summary

* Pagination, auto-refresh, background sync.

---

Date: 2025-11-12 15:01 -0500 (Session 13)
Milestone: v0.4.4 – Diagnostics UX Polish

Summary

* Parallelized tests; better spinners.

---

Date: 2025-11-13 15:01 -0500 (Session 14)
Milestone: v0.4.5 – Async Cleanup + Diagnostic Timing

Summary

* Added per-service timings.

---

Date: 2025-11-13 15:01 -0500 (Session 15)
Milestone: v0.4.6 – Async Conversion Across UI Pages

Summary

* Removed all `requests`; full async UI.

---

Date: 2025-11-13 15:01 -0500 (Session

xxx

Date: 2025-11-13 01:05 -0500 (Session 15)
Author: Codex 5 (Developer)
Milestone: v0.4.6 – Async Conversion Across UI Pages

Summary

* Eliminated all synchronous `requests` usage from Productions, Jobs, Locations, and Medical Facilities UI.
* All HTTP now async via `httpx.AsyncClient`.
* Added spinner/button-disable patterns across pages.
* Auto-refresh timers run through `ui.run_task` to avoid blocking.

Changes

* Updated `app/ui/productions.py`, `app/ui/jobs.py`, `app/ui/locations.py`, `app/ui/medicalfacilities.py` to async.
* Unified toast and spinner logic.

Testing

* `python -m compileall app/ui`.

---

Date: 2025-11-13 01:45 -0500 (Session 16)
Author: Codex 5 (Developer)
Milestone: v0.4.7 – Inline Editing in Productions

Summary

* Added inline `ui.select` and `ui.date` editors.
* Added dirty-row tracking and paused auto-refresh during edits.
* Sync endpoint updated to accept only modified rows.

Changes

* `app/ui/productions.py` rebuild.
* `app/api/productions_api.py` accepts `operation: ui_sync`.
* `background_sync.map_production` extended to include end dates.

Testing

* Compiled UI + API.

---

Date: 2025-11-13 02:10 -0500 (Session 17)
Milestone: v0.4.7 – Productions Fetch Reliability

Summary

* Switched data loading to browser `fetch` via `ui.run_javascript`.
* Improved spinners and error toasts.

---

Date: 2025-11-13 02:25 -0500 (Session 18)
Milestone: v0.4.7 – Productions Fetch Timeout

Summary

* Increased browser fetch timeout to 8 seconds.
* Added clear timeout messaging.

---

Date: 2025-11-13 02:35 -0500 (Session 19)
Milestone: v0.4.7 – Productions Fetch Logging

Summary

* Added server-side logging around fetch lifecycle.

---

Date: 2025-11-13 15:01 -0500 (Session 20)
Milestone: v0.4.7 – Productions Table UX Foundation

Summary

* Finalized columns, normalized schema, editors, confirm prompts.
* Enriched cache mapper and sync endpoint.

---

Date: 2025-11-13 03:05 -0500 (Session 21)
Milestone: v0.4.7 – Schema/UI Binding Sync

Summary

* Synced UI bindings with normalized backend vocabulary.

---

Date: 2025-11-13 04:10 -0500 (Session 22)
Milestone: v0.4.7 – Slot Fixes & JS Cleanup

Summary

* Replaced decorator-style slot usage with NiceGUI‑compliant patterns.
* Eliminated malformed JS injections.

---

Date: 2025-11-13 04:40 -0500 (Session 23)
Milestone: v0.4.7 – Page-Context Enforcement

Summary

* Fixed blank table by ensuring all UI mutations run inside page context.
* Added `run_in_page_context` helper.

---

Date: 2025-11-13 05:00 -0500 (Session 24)
Milestone: v0.4.7 – Table Update Enforcement

Summary

* Forced `table.update()` after assigning `table.rows`.
* Normalized slot resolution.

---

Date: 2025-11-15 19:30 -0500 (Session 24.1)
Milestone: v0.4.7 – Slot Resolution Fix

Summary

* Cleaned up `_resolve_slot_row` and removed duplicate helpers.

---

Date: 2025-11-15 19:45 -0500 (Session 24.2)
Milestone: v0.4.7 – Slot Decorator Removal

Summary

* Removed all decorator-style slot usage due to NiceGUI 3.2.0 TypeError.

---

Date: 2025-11-15 20:05 -0500 (Session 24.3)
Milestone: v0.4.7 – Slot Pattern Documentation

Summary

* Documented safe slot patterns and NiceGUI 3.2.0 limitations.

---


# Source: DEV_NOTES-recreated.md

# DEV_TOOLS.md — ATLSApp Developer Tools & Guardrails

## Purpose

Authoritative reference for Codex 5.1 rules, NiceGUI guardrails, and the human workflows we follow when building ATLSApp.

## Codex 5.1 Rules (Quick Recall)

* Async-only HTTP in UI code (`httpx.AsyncClient`); browser fetch via `ui.run_javascript` (8s timeout wrapper).
* All UI mutations must execute in a valid NiceGUI page slot/context.
* Table slots: use context-managed slots or column `body` lambdas; avoid decorator-style `@table.add_slot` in NiceGUI 3.2.x.
* API paths must stay relative (`/api/...`) and should be built via `app.services.api_client`.
* Every change requires a `docs/DEV_NOTES.md` session entry (date, session, milestone, summary, changes, testing, notes).
* `python -m compileall <files>` must pass for touched modules before commit.
* Preserve imports/helpers/logging; do not remove behavior or env handling unless explicitly requested.

## Human Developer Workflows

### Core Tools

* VS Code with ChatGPT (Genie AI + Codex 5.1 extensions).
* `uvicorn app.main:fastapi_app --reload` for live server.
* Python venv for isolation; `.env` at repo root for Notion/Maps credentials.
* Logging: `logs/app.log`, JSONL jobs (`app/data/jobs.log`), feature logs (e.g., `logs/productions.log`).

### Required Checks Before Commit

1. `python -m compileall app`
2. Manual smoke: `/dashboard`, `/productions`, `/settings`, `/jobs`
3. Confirm background sync starts (console/logs show interval loop)
4. Update `docs/DEV_NOTES.md`

## NiceGUI Guardrails

* Never mutate DOM outside the page slot; timers/tasks must route through page context.
* After setting `table.rows`, call `table.update()` so changes propagate.
* Avoid decorator-style slots; use `with table.add_slot(...)` or column `body` lambdas.
* Keep browser JS snippets minimal (no leading newlines); prefer shared constants and the 8s timeout wrapper.
* Do not rely on `ui.get_client()` in async tasks; prefer server-side calls and relative URLs.

## API Development Rules

* Always return `{status, message, ...}`.
* Log jobs via `log_job()` on success and error.
* Maintain cache fallback behavior for Notion-backed endpoints.
* Handle missing credentials gracefully and surface clear user-facing messages.

## Sync & Background Tasks

* Background sync enabled via env (`PRODUCTIONS_SYNC_ENABLED`, interval minutes).
* Cache path: `app/data/productions_cache.json`; refresh after mapper/schema changes.
* When updating UI from timers/async helpers, ensure page context or server callbacks (avoid emit/JS bridges for state changes).

## Fetch Patterns

* Browser fetch for large datasets (e.g., productions) with 8s timeout + toast on failure.
* Server-side async for Notion updates/sync; never block the NiceGUI event loop.

## Logging & Diagnostics

* Use module loggers with actionable messages (operation, count, error).
* Ensure `logs/` exists before writing; keep severity aligned (INFO flow, WARNING/ERROR failures).
* Add feature-specific logs when debugging (e.g., `logs/productions.log`).

## Editable Tables (Productions Reference)

* Prefer server-side handlers in column `body` lambdas or context slots; avoid client `emit` bridges for edits.
* Dirty-row tracking must update the source list and `table.rows`, then call `table.update()`.
* Auto-refresh should pause when dirty rows exist and resume after sync/discard.

## Deployment / Ops Notes

* `.env` auto-loads in `app/main.py`; maintain `NOTION_*`, `GOOGLE_MAPS_API_KEY`, and sync envs.
* Relative API paths keep dev/staging/prod aligned (no host/port hard-coding).
* Review `docs/DEV_NOTES.md` frequently for current patterns and pitfalls.

---

# DEV_NOTES.md - ATLS GUI App

(Full reconstructed sessions 1–24.3 follow below.)

Date: 2025-11-09 18:59 -0500
Author: Codex 5 (Developer)
Milestone: v0.3 – Job Logging System

Summary

* Implemented lightweight job logger and integrated with API routes.
* Added `/api/jobs/logs` endpoint to expose logs to the UI.
* Updated API map documentation.

Changes

* Added `app/services/logger.py` providing `log_job()` and `read_logs()` using JSONL at `app/data/jobs.log`.
* Updated `app/api/locations_api.py` to log success/error for `/api/locations/process`.
* Updated `app/api/facilities_api.py` to log success/error for `/api/facilities/fetch`.
* Added `app/api/jobs_api.py` with `GET /api/jobs/logs` returning `{status, message, logs}`.
* Fixed router registration order and included Jobs router in `app/main.py`.

Testing

* Module import sanity: ensured API modules import and logger reads/writes without raising exceptions locally.
* Endpoints return JSON with `status` and `message`.

Notes

* UI page `app/ui/jobs.py` currently static.

---

Date: 2025-11-09 19:01 -0500 (Session 2)
Milestone: v0.3.1 - Live Jobs Log UI

Summary

* Connected Jobs UI to logs endpoint.
* Added badges, toggles, refresh.

---

Date: 2025-11-09 19:01 -0500 (Session 3)
Milestone: v0.3.1 - Live Jobs Log UI (Docs sync)

Summary

* Standardized JSON responses.

---

Date: 2025-11-09 19:01 -0500 (Session 4)
Milestone: v0.3.1 - Stabilization

Summary

* Restored Config shim.
* Fixed bootstrap.

---

Date: 2025-11-09 19:01 -0500 (Session 5)
Milestone: v0.3.2 - Log Pruning & Rotation

Summary

* Added pruning + archive.

---

Date: 2025-11-09 19:01 -0500 (Session 6)
Milestone: v0.3.3 – Settings Connection Tests

Summary

* Added Notion + Maps diagnostics.

---

Date: 2025-11-09 19:01 -0500 (Session 7)
Milestone: v0.3.4 – Jobs UI Enhancements

Summary

* Filtering, archive, highlight.

---

Date: 2025-11-09 19:01 -0500 (Session 8)
Milestone: v0.3.4 – Hotfix

Summary

* Restored productions stub.

---

Date: 2025-11-09 15:01 -0500 (Session 8.1)
Milestone: v0.3.4.1 – Diagnostics Logging

Summary

* Added logs for settings tests.

---

Date: 2025-11-09 15:01 -0500 (Session 8.2)
Milestone: v0.3.4.2 – File-based Logging

Summary

* Added logs/app.log handler.

---

Date: 2025-11-09 15:01 -0500 (Session 8.3)
Milestone: v0.3.4.2 – API Path Standardization Fix

Summary

* Relative-path builder added.

---

Date: 2025-11-10 15:01 -0500 (Session 9)
Milestone: v0.4.0 – Dashboard Kickoff

Summary

* Dashboard page + `/api/dashboard/summary`.

---

Date: 2025-11-10 15:01 -0500 (Session 10)
Milestone: v0.4.1 – Dashboard Hardening & Env Autoload

Summary

* Fixed slot errors; timestamps local.

---

Date: 2025-11-09 15:01 -0500 (Session 11)
Milestone: v0.4.2 – Productions Data View & Sync

Summary

* Added `/productions` UI + fetch/sync.

---

Date: 2025-11-09 15:01 -0500 (Session 12)
Milestone: v0.4.3 – UI Enhancements & Background Sync

Summary

* Pagination, auto-refresh, background sync.

---

Date: 2025-11-12 15:01 -0500 (Session 13)
Milestone: v0.4.4 – Diagnostics UX Polish

Summary

* Parallelized tests; better spinners.

---

Date: 2025-11-13 15:01 -0500 (Session 14)
Milestone: v0.4.5 – Async Cleanup + Diagnostic Timing

Summary

* Added per-service timings.

---

Date: 2025-11-13 15:01 -0500 (Session 15)
Milestone: v0.4.6 – Async Conversion Across UI Pages

Summary

* Removed all `requests`; full async UI.

---

Date: 2025-11-13 15:01 -0500 (Session

xxx

Date: 2025-11-13 01:05 -0500 (Session 15)
Author: Codex 5 (Developer)
Milestone: v0.4.6 – Async Conversion Across UI Pages

Summary

* Eliminated all synchronous `requests` usage from Productions, Jobs, Locations, and Medical Facilities UI.
* All HTTP now async via `httpx.AsyncClient`.
* Added spinner/button-disable patterns across pages.
* Auto-refresh timers run through `ui.run_task` to avoid blocking.

Changes

* Updated `app/ui/productions.py`, `app/ui/jobs.py`, `app/ui/locations.py`, `app/ui/medicalfacilities.py` to async.
* Unified toast and spinner logic.

Testing

* `python -m compileall app/ui`.

---

Date: 2025-11-13 01:45 -0500 (Session 16)
Author: Codex 5 (Developer)
Milestone: v0.4.7 – Inline Editing in Productions

Summary

* Added inline `ui.select` and `ui.date` editors.
* Added dirty-row tracking and paused auto-refresh during edits.
* Sync endpoint updated to accept only modified rows.

Changes

* `app/ui/productions.py` rebuild.
* `app/api/productions_api.py` accepts `operation: ui_sync`.
* `background_sync.map_production` extended to include end dates.

Testing

* Compiled UI + API.

---

Date: 2025-11-13 02:10 -0500 (Session 17)
Milestone: v0.4.7 – Productions Fetch Reliability

Summary

* Switched data loading to browser `fetch` via `ui.run_javascript`.
* Improved spinners and error toasts.

---

Date: 2025-11-13 02:25 -0500 (Session 18)
Milestone: v0.4.7 – Productions Fetch Timeout

Summary

* Increased browser fetch timeout to 8 seconds.
* Added clear timeout messaging.

---

Date: 2025-11-13 02:35 -0500 (Session 19)
Milestone: v0.4.7 – Productions Fetch Logging

Summary

* Added server-side logging around fetch lifecycle.

---

Date: 2025-11-13 15:01 -0500 (Session 20)
Milestone: v0.4.7 – Productions Table UX Foundation

Summary

* Finalized columns, normalized schema, editors, confirm prompts.
* Enriched cache mapper and sync endpoint.

---

Date: 2025-11-13 03:05 -0500 (Session 21)
Milestone: v0.4.7 – Schema/UI Binding Sync

Summary

* Synced UI bindings with normalized backend vocabulary.

---

Date: 2025-11-13 04:10 -0500 (Session 22)
Milestone: v0.4.7 – Slot Fixes & JS Cleanup

Summary

* Replaced decorator-style slot usage with NiceGUI‑compliant patterns.
* Eliminated malformed JS injections.

---

Date: 2025-11-13 04:40 -0500 (Session 23)
Milestone: v0.4.7 – Page-Context Enforcement

Summary

* Fixed blank table by ensuring all UI mutations run inside page context.
* Added `run_in_page_context` helper.

---

Date: 2025-11-13 05:00 -0500 (Session 24)
Milestone: v0.4.7 – Table Update Enforcement

Summary

* Forced `table.update()` after assigning `table.rows`.
* Normalized slot resolution.

---

Date: 2025-11-15 19:30 -0500 (Session 24.1)
Milestone: v0.4.7 – Slot Resolution Fix

Summary

* Cleaned up `_resolve_slot_row` and removed duplicate helpers.

---

Date: 2025-11-15 19:45 -0500 (Session 24.2)
Milestone: v0.4.7 – Slot Decorator Removal

Summary

* Removed all decorator-style slot usage due to NiceGUI 3.2.0 TypeError.

---

Date: 2025-11-15 20:05 -0500 (Session 24.3)
Milestone: v0.4.7 – Slot Pattern Documentation

Summary

* Documented safe slot patterns and NiceGUI 3.2.0 limitations.

---


# Source: DEV_NOTES.md

# DEV_TOOLS.md — ATLSApp Developer Tools & Guardrails

## Purpose
Authoritative reference for Codex 5.1 rules, NiceGUI guardrails, and the human workflows we follow when building ATLSApp.

## Codex 5.1 Rules (Quick Recall)
- Async-only HTTP in UI code (`httpx.AsyncClient`); browser fetch via `ui.run_javascript` (8s timeout wrapper).
- All UI mutations must execute in a valid NiceGUI page slot/context.
- Table slots: use context-managed slots or column `body` lambdas; avoid decorator-style `@table.add_slot` in NiceGUI 3.2.x.
- API paths must stay relative (`/api/...`) and should be built via `app.services.api_client`.
- Every change requires a `docs/DEV_NOTES.md` session entry (date, session, milestone, summary, changes, testing, notes).
- `python -m compileall <files>` must pass for touched modules before commit.
- Preserve imports/helpers/logging; do not remove behavior or env handling unless explicitly requested.

## Human Developer Workflows
### Core Tools
- VS Code with ChatGPT (Genie AI + Codex 5.1 extensions).
- `uvicorn app.main:fastapi_app --reload` for live server.
- Python venv for isolation; `.env` at repo root for Notion/Maps credentials.
- Logging: `logs/app.log`, JSONL jobs (`app/data/jobs.log`), feature logs (e.g., `logs/productions.log`).

### Required Checks Before Commit
1) `python -m compileall app`
2) Manual smoke: `/dashboard`, `/productions`, `/settings`, `/jobs`
3) Confirm background sync starts (console/logs show interval loop)
4) Update `docs/DEV_NOTES.md`

## NiceGUI Guardrails
- Never mutate DOM outside the page slot; timers/tasks must route through page context.
- After setting `table.rows`, call `table.update()` so changes propagate.
- Avoid decorator-style slots; use `with table.add_slot(...)` or column `body` lambdas.
- In NiceGUI 3.2.x, `add_slot` is a context manager (or template string), not a callable; define slot content inside `with table.add_slot('body-cell-...'):` and bind loop variables via default args. Do not put Python callables in `columns` (functions are not JSON-serializable at render time).
- Keep browser JS snippets minimal (no leading newlines); prefer shared constants and the 8s timeout wrapper.
- Do not rely on `ui.get_client()` in async tasks; prefer server-side calls and relative URLs.

## API Development Rules
- Always return `{status, message, ...}`.
- Log jobs via `log_job()` on success and error.
- Maintain cache fallback behavior for Notion-backed endpoints.
- Handle missing credentials gracefully and surface clear user-facing messages.

## Sync & Background Tasks
- Background sync enabled via env (`PRODUCTIONS_SYNC_ENABLED`, interval minutes).
- Cache path: `app/data/productions_cache.json`; refresh after mapper/schema changes.
- When updating UI from timers/async helpers, ensure page context or server callbacks (avoid emit/JS bridges for state changes).

## Fetch Patterns
- Browser fetch for large datasets (e.g., productions) with 8s timeout + toast on failure.
- Server-side async for Notion updates/sync; never block the NiceGUI event loop.

## Logging & Diagnostics
- Use module loggers with actionable messages (operation, count, error).
- Ensure `logs/` exists before writing; keep severity aligned (INFO flow, WARNING/ERROR failures).
- Add feature-specific logs when debugging (e.g., `logs/productions.log`).

## Editable Tables (Productions Reference)
- Prefer server-side handlers in column `body` lambdas or context slots; avoid client `emit` bridges for edits.
- Dirty-row tracking must update the source list and `table.rows`, then call `table.update()`.
- Auto-refresh should pause when dirty rows exist and resume after sync/discard.

## Deployment / Ops Notes
- `.env` auto-loads in `app/main.py`; maintain `NOTION_*`, `GOOGLE_MAPS_API_KEY`, and sync envs.
- Relative API paths keep dev/staging/prod aligned (no host/port hard-coding).
- Review `docs/DEV_NOTES.md` frequently for current patterns and pitfalls.

---
This file should be updated whenever workflows, guardrails, or Codex rules evolve.

---

Date: 2025-11-21 14:30 -0500 (Session 27)
Author: Codex 5 (Developer)
Milestone: v0.4.8 — Productions Layout & UX Improvements

Summary
- Added horizontal overflow wrapper and min-width to the productions table so it stays beside the sidebar and scrolls horizontally.
- Injected global CSS to left-align all table headers and cells.
- Condensed LocationsTable to a short “Link” and made ProductionID link to `/production/<id>`.
- Inline editing is on hold; table is read-only while fetch/search/filter/pagination/auto-refresh remain unchanged.

Changes
- `app/ui/productions.py`: head CSS injection; `overflow-x-auto` wrapper with `min-w-[1600px]`; ProductionID link body; LocationsTable “Link” body; removed inline editing controls.
- `docs/PROJECT_HANDBOOK.md`: added UI conventions (overflow wrapper, left alignment, ID links) and version bumped to v0.4.8.
- `README.md`: version bumped to v0.4.8; documented layout scroll, left alignment, LocationsTable “Link,” and ProductionID navigation.

Testing
- `python -m compileall app`
- Manual: `/productions` (table beside sidebar, horizontal scroll, left alignment, LocationsTable shows “Link,” ProductionID clickable, no editing controls)
- Manual smoke: `/dashboard`, `/settings`, `/jobs`

Notes
- Follow NiceGUI 3.2.x slot guidance (lambda/context slots only). Editing remains paused per requirements.

Date: 2025-11-21 18:00 -0500 (Session 28)
Author: Codex 5 (Developer)
Milestone: v0.4.9 - Productions Page Notion Link Integration

Summary
- Added `NotionURL` (Notion page `url`) during row normalization.
- ProductionID now hyperlinks to the Notion page when `NotionURL` is present; falls back to text otherwise.
- No changes to fetch, filters, pagination, auto-refresh, or other UX refinements.

Changes
- `app/ui/productions.py`: normalize_row includes `NotionURL`; ProductionID column uses a slot/template to link to Notion.
- Docs updated to v0.4.9: README (Productions note), PROJECT_HANDBOOK (authoritative link convention), DEV_NOTES (this entry).

Testing
- `python -m compileall app`
- Manual: `/productions` (ProductionID hyperlinks to Notion; horizontal scroll; left alignment; LocationsTable "Link"; no editing controls; no slot/JS errors)
- Smoke: `/dashboard`, `/settings`, `/jobs`

Notes
- Notion’s built-in `url` is stable; no API changes required (UI-only enhancement).

---

Date: 2025-11-21 19:15 -0500 (Session 29)
Author: Codex 5 (Developer)
Milestone: v0.4.10 - Global Layout Improvements

Summary
- Added `no-wrap` root container and `shrink-0` sidebar to prevent wrapping beneath the sidebar.
- Main content now uses `overflow-x-auto`; header made sticky (`sticky top-0 z-10`).
- Optional `max-w-[1600px]` wrapper for readability on very wide screens; overall layout consistency improved.

Changes
- `app/ui/layout.py`: root row `no-wrap items-start`, sidebar `shrink-0`, main content `overflow-x-auto`, sticky header, max-width wrapper around page content.
- Docs updated to v0.4.10: README (layout enhancements), PROJECT_HANDBOOK (layout conventions), DEV_NOTES (this entry).

Testing
- `python -m compileall app`
- Manual: `/dashboard`, `/productions`, `/locations`, `/facilities`, `/jobs`, `/settings`; verify sidebar stays left, no wrapping, productions table stays right of sidebar, horizontal scroll works, sticky header visible, no slot/JS errors.

Notes
- UI-only layout adjustment; no API or page content changes. Layout complies with NiceGUI flex rules.

---

Date: 2025-11-21 20:00 -0500 (Session 30)
Author: Codex 5 (Developer)
Milestone: v0.4.11 - Global Theme System + Material Table Styles

Summary
- Added global Light/Dark mode toggle in the header and unified Material-style table styling (light + dark variants) via a single global CSS block.
- Removed per-page table CSS; styling now applies everywhere.

Changes
- `app/ui/layout.py`: introduced `ui.dark_mode()`, header toggle button/label, global table CSS, retained sticky header and layout; other pages unchanged.
- `app/ui/productions.py` (and other UI pages): removed per-page CSS injection (global styling handles tables).
- Docs: README, PROJECT_HANDBOOK, DEV_NOTES updated to v0.4.11 with theme/table styling notes.

Testing
- `python -m compileall app`
- Manual: toggle theme on `/dashboard`, `/productions`, `/locations`, `/facilities`, `/jobs`, `/settings`; confirm table headers styled, dark mode applies to headers/body, sticky header and sidebar unchanged, no slot/JS errors.

Notes
- UI-only; no API changes. Theme is managed globally via NiceGUI `ui.dark_mode()`.

---

Date: 2025-11-21 21:00 -0500 (Session 31)
Author: Codex 5 (Developer)
Milestone: v0.4.11 - Theme & Table Style Fixes

Summary
- Fixed dark mode coverage by adding dark backgrounds to page containers; refined header dark styles.
- Improved table header alignment/vertical centering: left justification, nowrap headers/cells, and consistent spacing in dark and light themes.

Changes
- `app/ui/layout.py`: extended global CSS with dark page backgrounds, left/centered header content (`.q-table__th-content`), nowrap headers/cells, and dark header border/background; header row gets dark classes.
- No per-page overrides added; styling remains global.

Testing
- `python -m compileall app`
- Manual: toggle theme on `/productions` and other pages; verify full dark background, left-aligned headers/cells, consistent vertical centering, no slot/JS errors.

Notes
- UI-only styling tweaks; no API or page content changes.

Date: 2025-11-21 21:45 -0500 (Session 32)
Author: Codex 5 (Developer)
Milestone: v0.4.12 - Final Table Header Alignment Fix + CSS Simplification

Summary
- Finalized table header alignment by targeting Quasar utility classes (`.text-right`, `.text-center`, `justify-*`) and aligning sort icons left.
- Simplified and consolidated the global table CSS in `layout.py` into organized sections (light, dark, alignment overrides).
- No functional changes; styling only.

Changes
- `app/ui/layout.py`: cleaned global CSS, added final header alignment override block, retained Material header styling and dark mode support.
- Docs bumped to v0.4.12: README, PROJECT_HANDBOOK, DEV_NOTES updated with alignment/CSS consolidation notes.

Testing
- `python -m compileall app`
- Manual: `/dashboard`, `/productions`, `/locations`, `/facilities`, `/jobs`, `/settings`; verify all headers left-aligned, sort icons left, dark mode alignment intact, no slot/JS errors, sticky header and sidebar unchanged.

Notes
- Alignment is now governed centrally in `layout.py`; no per-page alignment CSS should be added.

Date: 2025-11-22 10:00 -0500 (Session 33)
Author: Codex 5 (Developer)
Milestone: v0.4.13 - Dark Mode Polish, Persistent Theme, Typography

Summary
- Made header and sidebar fully reactive to theme with lambda-based classes; refined content background switching.
- Theme toggle button now reactive; removed Light/Dark label; added theme persistence via localStorage with `dark_mode_on`.
- Consolidated global CSS with typography (Inter/Segoe UI/Arial @15px) and kept alignment overrides.

Changes
- `app/ui/layout.py`: reactive header/sidebar/content classes, reactive toggle styling, theme persistence JS + `dark_mode_on` expose, consolidated CSS sections (base, light/dark, alignment, typography).
- Docs: README, PROJECT_HANDBOOK, DEV_NOTES updated to v0.4.13 and new styling/persistence rules.

Testing
- `python -m compileall app`
- Manual: toggle light/dark; verify header, sidebar, content backgrounds switch; theme persists on reload; table alignment unchanged; no slot/JS errors.

Notes
- UI-only changes; no API updates. Theme and styling are centralized in `layout.py`.

Date: 2025-11-21 19:15 -0500 (Session 29)
Author: Codex 5 (Developer)
Milestone: v0.4.10 - Global Layout Improvements

Summary
- Added `no-wrap` root container and `shrink-0` sidebar to prevent wrapping beneath the sidebar.
- Main content now uses `overflow-x-auto`; header made sticky (`sticky top-0 z-10`).
- Optional `max-w-[1600px]` wrapper for readability on very wide screens; overall layout consistency improved.

Changes
- `app/ui/layout.py`: root row `no-wrap items-start`, sidebar `shrink-0`, main content `overflow-x-auto`, sticky header, max-width wrapper around page content.
- Docs updated to v0.4.10: README (layout enhancements), PROJECT_HANDBOOK (layout conventions), DEV_NOTES (this entry).

Testing
- `python -m compileall app`
- Manual: `/dashboard`, `/productions`, `/locations`, `/facilities`, `/jobs`, `/settings`; verify sidebar stays left, no wrapping, productions table stays right of sidebar, horizontal scroll works, sticky header visible, no slot/JS errors.

Notes
- UI-only layout adjustment; no API or page content changes. Layout complies with NiceGUI flex rules.
