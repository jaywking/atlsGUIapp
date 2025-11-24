Refer to README.md and PROJECT_HANDBOOK.md for architecture and workflow rules.

Current Version: v0.4.17



# Source: DEV_NOTES_COMPLETE.md

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

### PowerShell CLI Rules (Cross-Platform Guardrail)

Codex must not generate Unix-only tools (`sed`, `awk`, `grep`, `cut`, etc.) in any PowerShell command. These tools are not available by default on Windows and will fail under `pwsh`.

When extracting line ranges, searching, or transforming text in PowerShell,
always use native PowerShell commands:

- Use `Get-Content` with array slicing:
    (Get-Content <file>)[<start_index>..<end_index>]

- For safer range handling:
    Get-Content <file> | Select-Object -Index (<start-1>)..(<end-1>)

- For searching:
    Select-String -Path <file> -Pattern <pattern>

Codex must never emit calls like:

    sed -n '115,190p' file.md

Instead, use:

    (Get-Content 'file.md')[114..189]

This rule applies to all PowerShell contexts, including calls executed via
`pwsh -Command`.

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

---

Date: 2025-11-22 10:15 -0500 (Session 34)
Author: Codex 5 (Developer)
Milestone: v0.4.14 - Content Wrapper & Header Dark Mode Completion

Summary
- Extended the global content wrapper styling so every page inherits correct light/dark backgrounds and text colors.
- Documented the new requirement for page-level header sections to use the shared class set.

Changes
- `app/ui/layout.py`: added explicit light/dark classes to the page content column to cover all routes.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: bumped version references to v0.4.14, added the new UI convention, and logged this session.

Testing
- `python -m compileall app`

Notes
- After deploying, manually verify dark-mode toggling on each route to ensure header blocks follow the updated styling.

---

Date: 2025-11-22 12:05 -0500 (Session 34b)
Author: Codex 5 (Developer)
Milestone: v0.4.14b - Header Dark Mode Override & Unified Page Header Blocks

Summary
- Applied dark-mode override for the global header bar to ensure Quasar wrappers cannot override the theme.
- Standardized all page-level header blocks with the Option A solid section style and removed page titles/subtitles across every page.

Changes
- `app/ui/layout.py`: added targeted dark-mode CSS overrides for the global header.
- `app/ui/dashboard.py`, `app/ui/productions.py`, `app/ui/locations.py`, `app/ui/medicalfacilities.py`, `app/ui/jobs.py`, `app/ui/settings.py`: removed page titles/subtitles and wrapped top controls in the unified header block with light/dark classes and borders.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: bumped version to v0.4.14b, documented the unified header style, and logged this session.

Testing
- `python -m compileall app`

Notes
- Verify light/dark toggling on all routes to confirm header blocks and the global header respect the unified styling without regressions.

---

Date: 2025-11-23 09:40 -0500 (Session 35)
Author: Codex 5 (Developer)
Milestone: v0.4.15b - Dark-Mode Wiring Fix

Summary
- Unified dark-mode wiring so Quasar’s `body--dark`, Tailwind `dark:` utilities, and theme persistence stay in sync. Ensured global header and page header blocks respond correctly.

Changes
- `app/ui/layout.py`: synchronized `body--dark` with a `dark` class for Tailwind, updated persistence to watch `body--dark`, and added targeted overrides for `atls-global-header` and `atls-page-header`.
- `app/ui/dashboard.py`, `app/ui/productions.py`, `app/ui/locations.py`, `app/ui/medicalfacilities.py`, `app/ui/jobs.py`, `app/ui/settings.py`: applied the standardized header block class with spacing/border updates.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: documented the unified dark-mode approach and version bump.

Testing
- `python -m compileall app`

Notes
- Validate light/dark toggling across all routes to ensure headers and wrappers switch cleanly without flicker.

---

Date: 2025-11-23 19:05 -0500 (Session 35.1)
Author: Codex 5 (Developer)
Milestone: v0.4.15c - Guarded Dark-Mode Wiring for SPA Navigation

Summary
- Added a one-time guard around the theme observers to prevent duplicate MutationObservers during SPA-style navigation while keeping Quasar `body--dark`, Tailwind `dark:`, and localStorage persistence aligned.

Changes
- `app/ui/layout.py`: wrapped theme init in a global guard to avoid repeated observer attachment and potential client slowdown.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: bumped version to v0.4.15c and recorded this guard fix.

Testing
- `python -m compileall app`

Notes
- After restart, verify light/dark toggling across routes and monitor load time to confirm the guard eliminates observer buildup and hanging.

---

Date: 2025-11-24 09:20 -0500 (Session 38)
Author: Codex 5 (Developer)
Milestone: v0.4.16 - Dark-Mode Stabilization

Summary
- Removed all custom theme MutationObservers and Tailwind bridging to rely solely on Quasar’s `body--dark`.
- Simplified dark-mode CSS to cover global header, page headers, and tables without JS side effects.

Changes
- `app/ui/layout.py`: deleted theme JS observers/persistence, pruned Tailwind bridge rules, and consolidated `body--dark` CSS for layout, headers, and tables.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: updated versioning and documented the dark-mode stabilization approach.

Testing
- `python -m compileall app`

Notes
- Restart the server and verify light/dark toggling on all routes; the UI should mount promptly with no freezes or console errors.

---

Date: 2025-11-24 10:05 -0500 (Session 39)
Author: Codex 5 (Developer)
Milestone: v0.4.17 - Dark Mode Follow-up Note

Summary
- Documented that dark mode remains inconsistent and will be revisited in a future release while keeping the UI responsive.

Changes
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: updated to v0.4.17 and added a note that dark mode needs a future fix.

Testing
- Documentation-only change.

Notes
- Dark mode remains a known issue; defer fixes to a future milestone.
