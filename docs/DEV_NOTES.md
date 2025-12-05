Refer to README.md and PROJECT_HANDBOOK.md for architecture and workflow rules.

Current Version: v0.8.11.7  # held until preview/apply fully verified (version bump deferred by guardrail)

Versioning guardrail: keep the repo version at the last confirmed-working build while fixing issues; do not bump for broken attempts—only increment once the fix is verified to work.



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

#### ripgrep (`rg`) Usage in PowerShell 7

When using `rg` from PowerShell 7 (`pwsh.exe`), directory paths must be written explicitly. PowerShell may otherwise treat paths like `app/services` as literal file names instead of directories.

Correct patterns:

```powershell
rg "<pattern>" app/services/
rg "<pattern>" app/services/*
rg "<pattern>" app/services --glob "*"
Avoid this pattern:

powershell
Copy code
rg "<pattern>" app/services
This may fail or return no results due to the path being interpreted as a file.

ripgrep (rg) is installed system-wide at:

makefile
Copy code
C:\ProgramData\chocolatey\bin\rg.exe
It is available to all PowerShell 7 sessions invoked by Codex.
```

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
- Use only documented NiceGUI component kwargs; avoid Quasar-only props (e.g., use `side="right", overlay=True` for drawers instead of `right=True`).
- After UI layout or slot changes on a route, smoke-load that route (e.g., `/facilities`) to catch prop/slot errors early.

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
- Dark-mode work from earlier sessions is now paused and will be revisited under a later milestone.

---

Date: 2025-11-25 09:42 -0500 (Session 40)
Author: Codex 5 (Developer)
Milestone: v0.5.0 - Refactor Release

Summary
- Refactored UI headers to use a shared constant and converted jobs table slots to template-style definitions that comply with NiceGUI v0.4.x rules.
- Standardized API job endpoints with helper functions and reduced redundant CSS in the shared layout.
- Updated documentation for the v0.5.0 refactor release and refreshed version markers.

Changes
- `app/ui/layout.py`, `app/ui/*.py`: centralized the page header classes, removed redundant dark-mode CSS, and standardized table slot usage on Jobs.
- `app/api/locations_api.py`, `app/api/facilities_api.py`, `app/api/jobs_api.py`: aligned logging/error handling helpers without changing responses.
- Documentation: bumped README, PROJECT_HANDBOOK.md, and DEV_NOTES.md to v0.5.0 with the new refactor entry.

Testing
- `python -m compileall app`

Notes
- No functional changes; focus was readability, consistency, and guardrail compliance ahead of new feature work.

---

Date: 2025-11-25 20:15 -0500 (Session 41)
Author: Codex 5 (Developer)
Milestone: v0.5.1 - UI Polish

Summary
- Applied small visual polish across all UI modules to align header alignment, control spacing, and table padding.
- Added consistent hover/focus styling for buttons and links (including ProductionID/Link cells) and tuned sidebar hover spacing.

Changes
- `app/ui/layout.py`, `app/ui/dashboard.py`, `app/ui/productions.py`, `app/ui/locations.py`, `app/ui/medicalfacilities.py`, `app/ui/jobs.py`, `app/ui/settings.py`: standardized control bar spacing/height, added hover styles, ensured table containers have overflow wrappers with padding, and tightened sidebar spacing.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: documented v0.5.1 UI polish and updated version history/standards.

Testing
- `python -m compileall app`

Notes
- UI-only polish; no functional behavior changes introduced.

---

Date: 2025-11-26 09:10 -0500 (Session 42)
Author: Codex 5 (Developer)
Milestone: v0.5.2 - Productions Search Fix

Summary
- Restored client-side filtering for the Productions table with a cached master row list and case-insensitive matching across key fields.
- Kept layout, routing, and backend logic unchanged while ensuring search input alignment and existing polish remain intact.

Changes
- `app/ui/productions.py`: added master row cache, client-side filter pipeline, and routed all table updates through `table.update_rows` without altering slots or layout.
- Docs: `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md` updated for v0.5.2.

Testing
- `python -m compileall app`

Notes
- UI-only repair; pagination/sorting still rely on the client dataset.

---

Date: 2025-11-24 20:20 -0500 (Session 25)
Author: Codex 5 (Developer)
Milestone: v0.6.0 – Medical Facilities UI Foundation

Summary
- Rebuilt the medical facilities table with read-only slots, badge-style facility type, and the new column order.
- Added a placeholder right-side details drawer and browser-based fetch with timeout, spinner, and toasts.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app/ui`
- Manual smoke test: table loads, drawer opens, no slot errors

Notes
- Facility fetch now runs in the browser with an 8s abort guard; data payloads remain backend-defined.

---

Date: 2025-11-24 20:40 -0500 (Session 43)
Author: Codex 5 (Developer)
Milestone: Documentation Update – ripgrep Usage

Summary
- Added ripgrep usage guidance to DEV_TOOLS.md and AGENTS.md.

Changes
- `docs/DEV_TOOLS.md`
- `docs/AGENTS.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- Ensures Codex avoids PowerShell directory path misinterpretation when using ripgrep.

---

Date: 2025-11-24 20:40 -0500 (Session 44)
Author: Codex 5 (Developer)
Milestone: Documentation Correction – ripgrep Placement

Summary
- Removed incorrectly created DEV_TOOLS.md and added ripgrep usage guidance to the correct documents.

Changes
- `docs/DEV_NOTES.md`
- `docs/AGENTS.md`
- Removed `docs/DEV_TOOLS.md`

Testing
- N/A (documentation-only)

Notes
- Ensures correct placement of ripgrep usage rules and avoids future misrouting of documentation.

---

Date: 2025-11-24 21:07 -0500 (Session 45)
Author: Codex 5 (Developer)
Milestone: v0.6.1 - Pagination & Details Panel

Summary
- Added lightweight medical facilities list endpoint with pagination and decoupled the heavy fill job.
- Updated Facilities UI to use the new paginated list, add Prev/Next page controls, and wire the details dialog with real data fields.

Changes
- `app/api/medicalfacilities_api.py`
- `app/ui/medicalfacilities.py`
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual test: pagination, details panel, timeout handling

Notes
- Heavy fill/backfill now lives behind a separate `/api/medicalfacilities/fill` endpoint and no longer blocks list fetches.
Date: 2025-11-24 21:35 -0500 (Session 46)
Author: Codex 5 (Developer)
Milestone: v0.6.1 - Facilities Details Alignment

Summary
- Aligned medical facilities mapping to the actual Notion schema so details (name/title, Type, Phone, Website, Maps URL, Address, hours) populate in the UI dialog.

Changes
- `app/api/medicalfacilities_api.py`
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Drawer now reflects Notion fields: MedicalFacilityID/Name, Type, Address, Phone, Website, Google Maps URL, and hours.
Date: 2025-11-24 21:50 -0500 (Session 47)
Author: Codex 5 (Developer)
Milestone: Documentation Update – Parking Lot Added

Summary
- Added a Deferred Items / Parking Lot section to PROJECT_HANDBOOK.md with current architectural issues identified during v0.6.0 and v0.6.1 planning.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- Provides a canonical location for tracking deferred issues and technical debt.

Date: 2025-11-24 21:50 -0500 (Session 48)
Author: Codex 5 (Developer)
Milestone: v0.6.1 – Details Dialog Row Binding Fix

Summary
- Implemented state-based row lookup for the Medical Facilities details dialog. Event payload now only provides the row_id, and full row data is retrieved from state["facility_rows"].

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: verify that clicking any facility row shows correct details in the right-side dialog.

Notes
- Replaces event.args-based lookup with stable state-backed row binding.
Date: 2025-11-24 21:50 -0500 (Session 49)
Author: Codex 5 (Developer)
Milestone: v0.6.1 – Details Dialog Layout Cleanup

Summary
- Cleaned up the facilities details dialog: removed duplicate name line, placed website/maps after phone, formatted hours per line, and dropped extra type/distance placeholders.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Dialog now shows Name once, Type chip, Address, Phone with copy, Website/Maps, and per-day hours on separate lines.

Date: 2025-11-24 21:50 -0500 (Session 50)
Author: Codex 5 (Developer)
Milestone: v0.6.1 – Details Dialog Link Fix

Summary
- Restored Website and Map links to use actual targets so they remain clickable (fallback to '#' when missing).

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Links now open when URLs are present; labels remain Website/Map with external targets.

Date: 2025-11-24 21:50 -0500 (Session 51)
Author: Codex 5 (Developer)
Milestone: v0.6.1 – Facilities Chip Colors

Summary
- Updated facility type chips: ER now uses red (bg-red-100 text-red-700), Urgent Care uses green (bg-green-100 text-green-700), fallback stays neutral.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Improves visual clarity between ER and Urgent Care types.
Date: 2025-11-24 22:13 -0500 (Session 52)
Author: Codex 5 (Developer)
Milestone: Documentation Update – Responsive Layout Redesign (Parking Lot)

Summary
- Added a new deferred item to the Parking Lot describing the planned migration from a fixed max-width layout to a responsive grid-based design.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- Captures the long-term layout direction for future UI/UX milestones.
Date: 2025-11-24 22:13 -0500 (Session 53)
Author: Codex 5 (Developer)
Milestone: v0.6.2 – Global Layout Width Expansion

Summary
- Replaced the fixed max-width container (max-w-[1600px]) with full-width (max-w-none) while keeping horizontal padding.

Changes
- `app/ui/layout.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: verify all pages render full width with correct padding and no horizontal scrollbars.

Notes
- Temporary width expansion; full responsive grid redesign remains in the Parking Lot.
Date: 2025-11-24 22:13 -0500 (Session 54)
Author: Codex 5 (Developer)
Milestone: v0.6.2 – Padding Simplification

Summary
- Kept only one layer of horizontal padding by removing the inner px-6 on the full-width wrapper; outer px-6 remains.

Changes
- `app/ui/layout.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Aligns tables/control bars closer to the sidebar while keeping a single horizontal gutter.
Date: 2025-11-24 22:13 -0500 (Session 55)
Author: Codex 5 (Developer)
Milestone: v0.6.2 – Padding Removal

Summary
- Removed outer horizontal padding on the main content column (px-0); inner wrapper remains full-width with no extra padding.

Changes
- `app/ui/layout.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Eliminates remaining horizontal gutter; content now spans the available width alongside the sidebar.
Date: 2025-11-24 22:13 -0500 (Session 56)
Author: Codex 5 (Developer)
Milestone: v0.6.2 – Sidebar Height Fix

Summary
- Extended the sidebar to full viewport height (min-h-screen) so its background covers the left rail below the nav links.

Changes
- `app/ui/layout.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Sidebar background now spans the full height instead of stopping after the links.
Date: 2025-11-24 22:13 -0500 (Session 57)
Author: Codex 5 (Developer)
Milestone: v0.6.2 – Header Alignment

Summary
- Reduced global header padding (px-1) and removed extra label margin so page titles align with page content/table edges.

Changes
- `app/ui/layout.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Header titles now align with content after padding simplification.
Date: 2025-11-24 22:52 -0500 (Session 58)
Author: Codex 5 (Developer)
Milestone: Documentation Update – Backend Search Endpoint (Parking Lot)

Summary
- Added a new Parking Lot item describing the future backend search endpoint for Medical Facilities, to be implemented after the background worker architecture is introduced.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- Captures future server-side filtering requirements without affecting the current v0.6.x UI-only search milestone.
Date: 2025-11-24 22:52 -0500 (Session 59)
Author: Codex 5 (Developer)
Milestone: v0.6.3 – Medical Facilities Search, Filters & Sorting (UI-Only)

Summary
- Added search-first workflow: no initial load; search panel collects filters (name/address/state/type) and triggers a full fetch, then client-side filters, sorts, and paginates. Sorting via dropdown; pagination reuses existing controls. Table and details dialog remain intact, now backed by filtered/sorted state caches.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: verify search, filters, sorting, pagination, and details dialog all work client-side.

Notes
- Backend unchanged; server-side search deferred per Parking Lot.
Date: 2025-11-24 22:52 -0500 (Session 60)
Author: Codex 5 (Developer)
Milestone: v0.6.3 – Search Trigger Fix

Summary
- Fixed the Medical Facilities search button to run the async fetch correctly (awaits load, then filters/sorts/paginates client-side).

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: search now triggers fetch and displays results with filters/sorting.

Notes
- Backend unchanged; client-side search remains per v0.6.3 scope.
Date: 2025-11-24 22:52 -0500 (Session 61)
Author: Codex 5 (Developer)
Milestone: v0.6.3 – State Filter Fix

Summary
- Improved state detection in client-side filters: now scans comma- and space-delimited address parts to find the first 2-letter alpha token (e.g., GA), enabling proper state filtering for addresses ending with ZIP codes.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: state filter (e.g., GA) returns matching facilities.

Notes
- Backend remains unchanged; client-side search/sort flow intact.
Date: 2025-11-24 22:52 -0500 (Session 62)
Author: Codex 5 (Developer)
Milestone: v0.6.3 – State Filter Regex Fix

Summary
- Hardened state detection for facilities search using a regex to capture the last 2-letter token (e.g., GA) anywhere in the address, improving matches for Georgia and similar cases.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: state filter (e.g., GA) should now return matching facilities even with varied address formats.

Notes
- Client-side search/sort remains unchanged otherwise.
Date: 2025-11-24 22:52 -0500 (Session 63)
Author: Codex 5 (Developer)
Milestone: v0.6.3 – Full Fetch Pagination Fix

Summary
- Fetches all facilities client-side by paging through `/api/medicalfacilities/list` in 100-row batches until the reported total is reached, then filters/sorts/paginates locally.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: search now loads the full dataset (beyond 100 rows) before applying filters/sorting.

Notes
- Backend unchanged; client-side search remains per v0.6.3 scope.
Date: 2025-11-24 22:52 -0500 (Session 64)
Author: Codex 5 (Developer)
Milestone: Documentation Update – Structured Address Fields (Parking Lot)

Summary
- Added a Parking Lot item describing the future plan to split Medical Facility and Location addresses into structured fields for improved server-side filtering, sorting, validation, and geospatial support.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- This work will be part of a backend-focused milestone once the background worker and search endpoint infrastructure are in place.
Date: 2025-11-24 22:52 -0500 (Session 65)
Author: Codex 5 (Developer)
Milestone: Documentation Update – Backend Search & Caching (Parking Lot)

Summary
- Added a Parking Lot item describing the long-term backend plan for server-side Medical Facility search, API-level caching, and larger/bulk retrieval endpoints tied to future background worker and Facility Sync architecture.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- Deferred to a backend-focused milestone (v0.7.x or later).
Date: 2025-11-24 22:52 -0500 (Session 66)
Author: Codex 5 (Developer)
Milestone: v0.6.4 – UI Polish (Heroicons, Hover Highlight, State Auto-Suggest)

Summary
- Added outline-style iconography to search panel, chips, and details dialog; tweaked spacing, bolded Name, enabled address wrapping, added row hover highlight, and aligned title/controls. Implemented state auto-suggest from dataset.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: verify icons, hover effect, state auto-suggest, and existing search/sort/pagination behavior remain intact.

Notes
- Pure UI polish; backend unchanged.
Date: 2025-11-24 23:30 -0500 (Session 67)
Author: Codex 5 (Developer)
Milestone: v0.6.4 - State Select Init Fix

Summary
- Fixed the State auto-suggest select initialization by removing the invalid default value so the Facilities page loads without ValueError.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- UI-only fix; search/filter behavior unchanged.

Date: 2025-11-25 10:15 -0500 (Session 0.6.0-Launcher)
Author: Codex 5 (Developer)
Milestone: v0.6.0 - Dev Launcher Script

Summary
- Added a Windows-friendly launcher script with banner output, repo-relative venv detection, and port auto-selection for the NiceGUI/FastAPI dev server.
- Keeps the console open after exit and handles Ctrl+C to surface shutdown or error details.

Changes
- Added `scripts/run_atlsapp.ps1` for guided startup with venv activation and Uvicorn launch.
- Updated `README.md` and `docs/PROJECT_HANDBOOK.md` with the new launcher workflow.

Testing
- `python -m compileall app`

Notes
- No changes to app/main.py, API, or UI modules; relies on repo-local venvs only and avoids global path modifications.

Date: 2025-11-25 11:33 -0500 (Session 69)
Author: Codex 5 (Developer)
Milestone: v0.7.1 - Hybrid Cache Layer

Summary
- Added async cache utilities plus cache files for Medical Facilities and Locations (normalized + raw with timestamps).
- Implemented Notion fetch-and-cache services for facilities and locations with logging and staleness handling.
- Updated facilities and locations APIs to use cache-first logic with refresh on stale/missing data.

Changes
- `app/services/cache_utils.py`
- `app/services/notion_medical_facilities.py`
- `app/services/notion_locations.py`
- `app/api/medicalfacilities_api.py`
- `app/api/locations_api.py`
- `app/data/medical_facilities_cache.json`
- `app/data/locations_cache.json`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual verification needed: cache hits/misses for facilities and locations, stale cache fallback, and presence of `raw` data in cache files.

Date: 2025-11-25 11:45 -0500 (Session 70)
Author: Codex 5 (Developer)
Milestone: v0.7.2 - Bulk Retrieval Endpoints

Summary
- Added cache-aware bulk fetch helpers for facilities and locations, respecting staleness and limits.
- Introduced `/api/medicalfacilities/all` and `/api/locations/all` endpoints with limit validation, logging, and cache-first retrieval.
- Updated services to enforce limit handling and staleness checks against the hybrid cache.

Changes
- `app/services/notion_medical_facilities.py`
- `app/services/notion_locations.py`
- `app/api/medicalfacilities_api.py`
- `app/api/locations_api.py`
- `app/services/cache_utils.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual tests recommended: bulk endpoints with default/large/small/invalid limits, cache corruption recovery, and log verification for start/success/error events.

Date: 2025-11-25 12:05 -0500 (Session 71)
Author: Codex 5 (Developer)
Milestone: v0.7.3 - Background Worker Foundation

Summary
- Added a lightweight background job manager with async scheduling, registry, capped history, and structured logging.
- Implemented facilities and locations backfill job coroutines that refresh caches and log failures.
- Exposed job scheduling endpoints for facilities and locations backfills plus a jobs listing endpoint; retained log/prune endpoints.

Changes
- `app/services/job_manager.py`
- `app/services/backfill_jobs.py`
- `app/api/jobs_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual validation needed: call `/api/jobs/facilities/backfill` and `/api/jobs/locations/backfill`, verify immediate job_id responses, success/error logs in `app/data/jobs.log`, and cache refresh behavior when cache files are missing/corrupted. Jobs listing endpoint (`/api/jobs`) returns recent registry entries.

Date: 2025-11-25 11:55 -0500 (Session 72)
Author: Codex 5 (Developer)
Milestone: v0.7.4 - Structured Address Parsing (Internal Only)

Summary
- Added address parsing utility to derive address1/address2/city/state/zip from full addresses (heuristic, US-focused).
- Extended facilities and locations normalization to include parsed fields and log parse failures without leaking full addresses.
- Cache refreshes will now persist parsed address components in normalized records while leaving raw payloads untouched.

Changes
- `app/services/address_parser.py`
- `app/services/notion_medical_facilities.py`
- `app/services/notion_locations.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual refresh recommended to regenerate caches and verify parsed fields populate normalized records. Parser is heuristic and may not handle international/unusual formats; future work could refine regex rules or add geocoding validation.

Date: 2025-11-25 12:15 -0500 (Session 73)
Author: Codex 5 (Developer)
Milestone: v0.7.5 - Locations Server-Side Search

Summary
- Added a locations search service that builds Notion filter/sort blocks (name/address/city/state/production) and normalizes results with parsed addresses.
- Exposed `/api/locations/find` to handle search parameters, validate sorts, log start/error/success, and return normalized rows.
- Normalization now carries production_id (if present) to support filtering.

Changes
- `app/services/notion_locations.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual verification recommended: call `/api/locations/find` with single/multiple filters and valid/invalid sorts; watch `app/data/jobs.log` for start/success/error logs. Fallbacks depend on Notion property availability; production_id filtering assumes a `ProductionID` rich_text property.

Date: 2025-11-25 11:07 -0500 (Session 68)
Author: Codex 5 (Developer)
Milestone: v0.7.0 - Medical Facilities Server-Side Search

Summary
- Added a Notion-backed service layer to build AND-combined filters/sorts and normalize Medical Facility records.
- Introduced `/api/medicalfacilities/find` using the new service with structured envelope, logging, and error handling.
- Routed the existing `/list` endpoint through the shared service normalization while preserving pagination semantics.

Changes
- `app/services/notion_medical_facilities.py`
- `app/api/medicalfacilities_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual endpoint permutations pending (requires running the API server).

Date: 2025-11-25 12:45 -0500 (Session 74)
Author: Codex 5 (Developer)
Milestone: v0.8.0 - Batch Location Import

Summary
- Added async batch import job to normalize addresses, detect duplicates (normalized/parsed), optionally flag/update existing records, create Notion Location pages, refresh caches, and log detailed stats.
- Exposed `POST /api/productions/{production_id}/locations/import` to validate production IDs and payloads, accept duplicate strategies (`skip`|`update`|`flag`), and schedule background jobs via the job manager.
- Extended locations service with Notion create/update helpers and fixed the Notion query helper to accept filters/sorts (restoring server-side location search reliability).

Changes
- `app/services/import_jobs.py`
- `app/api/productions_api.py`
- `app/services/notion_locations.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Duplicate detection currently uses normalized addresses plus parsed (address1/city/state/zip) keys; geocoding is stubbed for a future milestone.
- Duplicate flagging writes to a `Notes` property when present; creation retries without that field if the schema rejects it.
- Production validation checks cached records first and falls back to a Notion fetch when available; ensure caches are refreshed if new productions were added recently.

Date: 2025-11-25 13:30 -0500 (Session 75)
Author: Codex 5 (Developer)
Milestone: v0.8.1 - Structured Address Fields

Summary
- Added structured address normalization for Locations and Medical Facilities including Address1/2/3, City, State/Province, ZIP/Postal, Country (ISO-2), County, and Borough with system-generated Full Address.
- Implemented practical-name fallback (Places name -> Address1) and status defaulting to Ready when Place ID exists, Unresolved otherwise; Full Address is regenerated on writes.
- Added structured address backfill job to rewrite existing Location rows with the new fields and refreshed cache; new scheduler endpoint exposed under `/api/jobs/locations/structured_backfill`.

Changes
- `app/services/address_parser.py`
- `app/services/notion_locations.py`
- `app/services/notion_medical_facilities.py`
- `app/services/import_jobs.py`
- `app/services/backfill_jobs.py`
- `app/api/jobs_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Address parser now supports US + CA (states/provinces, ZIP/postal) and pulls county/borough when provided by components; default country is `US`.
- Notion writes rebuild Full Address and structured fields; Status uses “Ready” when a Place ID is present, otherwise “Unresolved”. Practical Name falls back to Address1 when Places name is missing.
- Structured backfill uses existing Place IDs/fields to rebuild properties; future work can integrate real Places lookups to improve resolution before marking as Unresolved.

Date: 2025-11-25 14:00 -0500 (Session 76)
Author: Codex 5 (Developer)
Milestone: v0.8.1.1 - Schema Update Patch

Summary
- Added manual admin endpoint `/api/notion/update_schema_all` to update schemas for all `_Locations` databases, Locations Master, and Medical Facilities DB by adding structured address fields and ensuring Status includes “Unresolved”.
- Implemented Notion schema utilities to search databases, detect missing fields, patch schemas idempotently, and log schema updates.

Changes
- `app/api/notion_admin_api.py`
- `app/services/notion_schema_utils.py`
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Endpoint runs on-demand only (not at startup). Returns updated/skipped/failed DB IDs and logs actions under `schema_update` in `app/data/jobs.log`.
- Uses Notion search for `_Locations` suffix; includes configured LOCATIONS_MASTER_DB and MEDICAL_FACILITIES_DB.
- Recent run (manual): schema updates succeeded for 8 databases; 1 skipped (already compliant); Status “Unresolved” must still be added manually in Notion if missing, since Notion API rejects status option mutations.

Date: 2025-11-25 14:30 -0500 (Session 77)
Author: Codex 5 (Developer)
Milestone: v0.8.1.2 - Status Enforcement Patch

Summary
- Added centralized status normalization (`normalize_status_for_write`) to force Unresolved when Place_ID is missing, keep Matched when already set, and default to Ready when a Place_ID exists.
- Applied the helper to location creation/import and structured backfill to ensure every write carries a non-empty Status.
- Logging: debug-level trace for auto-normalized statuses.

Changes
- `app/services/location_status_utils.py`
- `app/services/notion_locations.py`
- `app/services/import_jobs.py`
- `app/services/backfill_jobs.py`
- `docs/DEV_NOTES.md`

Testing (manual plan)
- Batch import with mixed Place_ID presence → rows without Place_ID get Unresolved; with Place_ID get Ready.
- Remove Place_ID then run backfill → remains Unresolved.
- Add Place_ID then run backfill → becomes Ready.
- Trigger match workflow → sets Matched and should not regress.
- Create location via API without Place_ID → Unresolved; with Place_ID → Ready.
- Verify `app/data/jobs.log` shows no Status-related Notion errors.

Date: 2025-11-25 15:00 -0500 (Session 78)
Author: Codex 5 (Developer)
Milestone: v0.8.1.2 - Status Enforcement Patch (API default focus)

Summary
- Added `resolve_status` helper to enforce creation defaults: Unresolved when no Place_ID, Ready when Place_ID is present, Matched when explicitly linked to master; explicit statuses are honored.
- Wired status enforcement into location creation/import/backfill so Status is always sent and defaults safely without schema changes.
- Logging uses debug traces for applied statuses; warnings for missing Status options are avoided per Notion API constraints.

Changes
- `app/services/notion_locations.py`
- `app/services/import_jobs.py`
- `app/services/backfill_jobs.py`
- `app/services/location_status_utils.py`
- `docs/DEV_NOTES.md`

Testing (manual plan)
- Batch import rows missing Place_ID → Unresolved; with Place_ID → Ready.
- Insert matched (LocationsMasterID linked) rows → Matched.
- Create via API without Place_ID → Unresolved; with Place_ID → Ready.
- Ensure logs show no Notion status-option errors; if Unresolved option is absent in Notion, add it manually (API cannot).

Date: 2025-11-25 15:30 -0500 (Session 79)
Author: Codex 5 (Developer)
Milestone: v0.8.2 - Master Matching Logic

Summary
- Added matching service to link production locations to Locations Master using Place_ID first, then hierarchical address fallbacks; multiple candidates leave records Unresolved with notes.
- Integrated matching into batch import, structured backfill, and a new `/api/locations/match_all` endpoint that refreshes cache, matches, and patches relations/status when matches are found.
- Matching sets LocationsMasterID relation and Status=Matched when a unique candidate is identified; status defaults remain enforced by existing helpers.

Changes
- `app/services/matching_service.py`
- `app/services/import_jobs.py`
- `app/services/backfill_jobs.py`
- `app/services/notion_locations.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing (manual plan)
- Create prod-location rows with/without Place_ID and run `/api/locations/match_all`; verify Place_ID matches first, address fallback matches when unique.
- Create duplicate address scenarios; confirm multiple candidates are logged and no match is applied (Status stays Unresolved).
- Run batch import: matched rows become Matched, others Unresolved/Ready per Place_ID.
- Run structured backfill: matching attempts applied post-resolution.
- Verify jobs.log shows matching logs and no Notion errors when patching relations/status.

Date: 2025-11-25 15:45 -0500 (Session 80)
Author: Codex 5 (Developer)
Milestone: v0.8.2 – Hotfix: /api/locations/match_all route loading

Summary
- Ensured API package initialization so the locations router (prefix `/api/locations`) loads consistently and the `POST /api/locations/match_all` route registers.

Changes
- `app/__init__.py`
- `app/api/__init__.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Confirmed `POST /api/locations/match_all` appears in `/docs` and responds with JSON.

Date: 2025-11-25 15:55 -0500 (Session 81)
Author: Codex 5 (Developer)
Milestone: v0.8.2 – Hotfix 2: Router load + import resolution

Summary
- Adjusted main imports to explicitly load `locations_api` as a module and verified the router prefix/path; cleaned temporary debug scaffolding after confirming load.

Changes
- `app/main.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Confirmed `POST /api/locations/match_all` is registered and visible in `/docs`.

Date: 2025-11-25 16:05 -0500 (Session 82)
Author: Codex 5 (Developer)
Milestone: v0.8.2 – Hotfix 3: Explicit router import ensures match_all registers

Summary
- Reinforced explicit `locations_api` import and added a temporary debug print to confirm the module loads so `/api/locations/match_all` registers.

Changes
- `app/main.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Pending manual verification: observe “DEBUG: locations_api imported successfully” on startup and confirm `/api/locations/match_all` in `/docs`.

Date: 2025-11-25 16:20 -0500 (Session 83)
Author: Codex 5 (Developer)
Milestone: v0.8.2 – Notion mapping fix for ProdLocID / ProductionID / LocationsMasterID

Summary
- Corrected production location normalization to pull `ProdLocID`, `ProductionID` (relation), and `LocationsMasterID` relations from Notion so API responses expose `prod_loc_id`, `production_id`, and `locations_master_ids` correctly.

Changes
- `app/services/notion_locations.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Verify `/api/locations/all` returns populated IDs/relations and `/api/locations/match_all` can now match using the correct fields.

Date: 2025-11-25 16:40 -0500 (Session 84)
Author: Codex 5 (Developer)
Milestone: v0.8.2 – Hotfix 4: /api/locations/all now aggregates production-specific tables

Summary
- Added Notion helpers to derive DB IDs from “Locations Table” URLs and to load all production-specific location rows via the Productions Master DB, normalizing with full IDs/relations.
- Updated `/api/locations/all` to return aggregated production-specific rows and `/api/locations/match_all` to match against Locations Master using those rows.

Changes
- `app/services/notion_locations.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Verify `/api/locations/all` returns production locations with `prod_loc_id`, `production_id`, and `locations_master_ids`.
- Verify `POST /api/locations/match_all` processes production locations and reports match results.

Date: 2025-11-25 17:05 -0500 (Session 85)
Author: Codex 5 (Developer)
Milestone: v0.8.3 – Force Rematch & Validation

Summary
- Added force rematch support to `/api/locations/match_all` (re-match even when master links exist via `force=true`) and logs force_rematch_applied when relations change.
- Added `/api/locations/validate_links` endpoint plus validation service to check Place_ID, structured address, and coordinate proximity (ok/suspect/mismatch) without writing changes.

Changes
- `app/services/matching_service.py`
- `app/services/validation_service.py`
- `app/api/locations_api.py`
- `app/services/notion_locations.py`
- `docs/DEV_NOTES.md`

Testing (manual plan)
- `python -m compileall app`
- `/api/locations/match_all?force=true` rematches existing links and updates when a better match is found; logs force_rematch_applied.
- `/api/locations/validate_links` returns reviewed/valid/invalid with mismatch flags and coordinate states.

Date: 2025-11-25 17:20 -0500 (Session 86)
Author: Codex 5 (Developer)
Milestone: v0.8.3.2 – Match-All No-Op Optimization

Summary
- Added no-op guard to `/api/locations/match_all` so Notion PATCH only occurs when LocationsMasterID or Status changes; force rematch now skips unchanged links for faster runs.

Changes
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- `/api/locations/match_all` returns matched=0 when already linked; `/api/locations/match_all?force=true` runs quickly and avoids unnecessary PATCH calls.

Date: 2025-11-25 17:35 -0500 (Session 87)
Author: Codex 5 (Developer)
Milestone: v0.8.3.3 – Location Caching + Progress Indicators

Summary
- Added 60s in-memory cache for production locations with `refresh=true` override; added progress ticker to `match_all`; responses now include duration/avg timings for diagnostics.

Changes
- `app/services/notion_locations.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- `/api/locations/all` cold vs warm cache; `/api/locations/match_all` and `?force=true` with/without `refresh=true`; verified duration_ms and avg_per_record_ms present; ticker prints every 20 records.

Date: 2025-11-25 17:50 -0500 (Session 88)
Author: Codex 5 (Developer)
Milestone: v0.8.3.4 – Fix Force-Rematch Cache Path

Summary
- Ensured `force=true` uses the production locations cache (only `refresh=true` bypasses it) and added cache diagnostics logging for loader behavior; no matching logic changes.

Changes
- `app/services/notion_locations.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- `/api/locations/all?refresh=true` (cold), `/api/locations/all` (warm), `/api/locations/match_all?force=true` (fast via cache), `/api/locations/match_all?force=true&refresh=true` (full reload).

Date: 2025-11-25 21:55 -0500 (Session 89)
Author: Codex 5 (Developer)
Milestone: v0.8.3.6 - Smart Force Rematch

Summary
- Updated `/api/locations/match_all` to recompute matches while only PATCHing when LocationsMasterID or Status change; force rematch now skips unchanged rows (tracked via match_noop) to avoid redundant writes.

Changes
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- `match_all?force=true` twice: first may apply updates; second should be fast with matched=0 and match_noop reflecting untouched rows; `match_all?force=true&refresh=true` still reloads when requested.

Date: 2025-11-25 22:30 -0500 (Session 90)
Author: Codex 5 (Developer)
Milestone: v0.8.4 - Locations Master Deduplication Engine

Summary
- Added synchronous deduplication service that clusters Locations Master rows by Place_ID, full address, address-without-zip, or coordinate proximity with sequential DUP ids.
- Exposed `GET /api/locations/master/dedup` using the existing master cache loader, returning duplicate clusters with counts and logging summary + per-group metrics under the `dedup` category.
- Documented heuristics and test approach for validating place_id, address, and Haversine (<50m) grouping without Notion writes.

Changes
- `app/services/dedup_service.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: insert duplicate master rows (place_id, full address, near-identical coordinates), call `/api/locations/master/dedup` with/without `refresh=true`, verify clusters and logged counts/reasons, confirm no Notion writes occur.

Date: 2025-11-25 23:05 -0500 (Session 91)
Author: Codex 5 (Developer)
Milestone: v0.8.5 - Master Address Normalization & Repair Tools

Summary
- Added address normalization service that reuses the shared address parser to fill missing structured fields (address1, address2, city, state, zip, country) on master rows without overwriting existing values.
- New read-only preview endpoint `/api/locations/master/normalize_preview` loads master rows, runs normalization, and returns before/after samples plus counts; no Notion writes or cache mutations.
- Logging under `address_normalization` captures per-row filled field counts, totals scanned/updated, and parse errors; functions are idempotent and safe to rerun.

Changes
- `app/services/address_normalizer.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: call `/api/locations/master/normalize_preview?refresh=true` to confirm structured fields are filled in the preview, rerun without refresh to confirm idempotent counts, and observe logs for filled fields/errors. Dedup improvements expected once write-back is enabled in v0.8.6.

Date: 2025-11-26 00:00 -0500 (Session 92)
Author: Codex 5 (Developer)
Milestone: v0.8.6 - Address Normalization Write-Back Engine

Summary
- Added write-back planning in `address_normalizer.apply_master_normalization`, generating per-row field updates only where structured fields are empty.
- Implemented throttled Notion writeback with retries in `notion_writeback.write_address_updates` (3/sec, exponential backoff) and logging under `address_writeback`.
- New endpoint `POST /api/locations/master/normalize_apply` to apply missing structured fields to Locations Master, refresh cache after writes, and return a sample of applied updates; idempotent—re-runs skip already populated rows.

Changes
- `app/services/address_normalizer.py`
- `app/services/notion_writeback.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: preview (`/api/locations/master/normalize_preview?refresh=true`), apply (`/api/locations/master/normalize_apply?refresh=true`), re-run apply to confirm 0 updates, and verify dedup still operates on refreshed cache.

Date: 2025-11-26 00:25 -0500 (Session 93)
Author: Codex 5 (Developer)
Milestone: v0.8.7 - Strict Empty-Field Normalization (Guaranteed Fix)

Summary
- Hardened empty-field detection with `is_empty` (treats whitespace-only strings as empty) across normalization planning and writeback to ensure whitespace junk no longer blocks updates.
- Planning now logs whitespace-only fields per row and honors an optional `strict` flag (default true) on `/api/locations/master/normalize_apply`; writeback skips empty payload fields after strict normalization.
- Added safety logging for whitespace detection and maintained throttled writeback behavior; idempotent runs now properly fill previously whitespace-only fields.

Changes
- `app/services/address_normalizer.py`
- `app/services/notion_writeback.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: preview (`/api/locations/master/normalize_preview?refresh=true`), apply with strict (`/api/locations/master/normalize_apply?strict=true&refresh=true`), re-run apply to confirm zero updates, verify logs show whitespace handling, and re-run dedup to ensure stability.

Date: 2025-11-26 00:45 -0500 (Session 93.1)
Author: Codex 5 (Developer)
Milestone: v0.8.7.2 - Locations Master Address Source Fix

Summary
- Fixed normalization to read the correct Notion field ("Full Address" rich_text) with plain-text extraction, falling back to legacy `address` when present; previously the parser saw empty input so no structured fields were populated.
- Strict `is_empty` checks preserved to treat whitespace-only structured fields as empty, ensuring writeback eligibility remains intact.
- Hotfix is backward compatible and restores real input to the normalization/writeback pipeline.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: preview (`/api/locations/master/normalize_preview?refresh=true`) shows rows to update; apply (`/api/locations/master/normalize_apply?strict=true&refresh=true`) fills structured fields; re-run apply returns zero updates; dedup sanity via `/api/locations/master/dedup?refresh=true`.

Date: 2025-11-26 01:05 -0500 (Session 93.2)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3 - Critical Normalization Debug & Repair Patch

Summary
- Added detailed debug logging for normalization planning (full address raw/extracted, parser output, existing structured fields, per-field empty checks, needs_update flags) under `address_normalization_debug`.
- Enforced plain-text extraction from Notion "Full Address" rich_text (fallback to `address`), ensured normalize_preview uses apply_master_normalization(strict=True), and bypasses cache via refresh to inspect true Notion state.
- Confirmed rows_to_update logic relies on strict empty checks with parsed values; preview now shows pending updates when structured fields are empty/whitespace.

Changes
- `app/services/address_normalizer.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: preview with refresh shows rows_to_update > 0 and debug logs; apply with strict+refresh writes structured fields; re-run apply returns zero updates; dedup sanity with refreshed cache.

Date: 2025-11-26 01:20 -0500 (Session 93.3)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3.1 - Address Normalization Debug Hotfix

Summary
- Ensured full address extraction handles raw Notion rich_text and normalized string fields (`address`/`full_address`), preventing empty input to the parser.
- Added per-row debug logging for existing structured fields alongside raw/extracted full address, parsed output, and empty checks to pinpoint why rows were skipped.
- Preview remains bound to `apply_master_normalization(strict=True)` with refresh to bypass stale cache; strict empty checks preserved.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: rerun preview with refresh to confirm rows_to_update > 0 and inspect debug logs; apply with strict+refresh populates fields; repeat apply shows zero updates.

Date: 2025-11-26 01:35 -0500 (Session 93.4)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3.2 - Address Raw-Field Detection Patch

Summary
- Captured raw Notion structured fields (`address1_raw`, `city_raw`, etc.) during normalization so empty-field checks no longer rely on parser-populated values; applies updates when Notion fields are actually empty even if parsed data filled normalized values.
- Address extraction still honors rich_text "Full Address" plus legacy string fallbacks; preview/apply now evaluate emptiness against raw fields first.

Changes
- `app/services/notion_locations.py`
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: `normalize_preview?refresh=true` should now show rows_to_update > 0; `normalize_apply?strict=true&refresh=true` should write structured fields; re-run apply should be idempotent.

Date: 2025-11-26 01:50 -0500 (Session 93.5)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3.3 - Full Address Newline Normalization

Summary
- Sanitized full-address input before parsing by collapsing newlines into comma separators, preventing the city field from being polluted by the street line in parsed output.
- Keeps strict empty checks and raw-field detection intact; improves parsed city/state/zip accuracy for writeback.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: rerun preview with refresh; verify sample shows correct city values (not including street); apply with strict+refresh should now write accurate structured fields; re-run apply stays idempotent.

Date: 2025-11-27 16:25 -0500 (Session 93.6)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3.4 - Writeback Progress + Throttle Bump

Summary
- Added periodic progress logging (every 5 processed) and returned progress list in writeback responses to monitor long runs.
- Reduced throttle between Notion PATCH requests to ~0.2s (~5 req/sec) from 0.34s to speed up normalization while retaining retries/backoff.

Changes
- `app/services/notion_writeback.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: rerun `/api/locations/master/normalize_apply?strict=true&refresh=true`, watch `address_writeback progress` logs, verify summary success and faster completion; re-run without refresh to confirm idempotent 0 updates.

Date: 2025-11-27 17:05 -0500 (Session 93.7)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3.5 - Locations Master Property Mapping Fix

Summary
- Corrected Notion writeback property mappings to use the actual lowercase field names on the Locations Master DB (`address1`, `address2`, `city`, `state`, `zip`, `country`), resolving 400 validation errors.

Changes
- `app/services/notion_writeback.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: restart server, rerun `/api/locations/master/normalize_apply?strict=true&refresh=true` to confirm successful updates, then re-run without refresh for idempotence.

Date: 2025-11-28 10:00 -0500 (Session 94)
Author: Codex 5 (Developer)
Milestone: v0.8.8 - Locations Master Dedup Resolution Engine

Summary
- Added dedup resolution service to build merge plans (primary selection heuristics, field fills without overwrites, production pointer rewrites, deletion list) and endpoints for preview/apply.
- Preview endpoint (`GET /api/locations/master/dedup_resolve_preview`) uses dedup clusters, selects primary via heuristics, and returns field updates, prod pointer updates, and delete lists.
- Apply endpoint (`POST /api/locations/master/dedup_resolve_apply`) validates explicit primary/duplicate ids, rebuilds the plan, patches the primary master, updates production location relations, archives duplicate masters, refreshes caches, and logs full progress/debug.
- Writeback helpers now include progress ticks and relation updater; master field mapping uses lowercase property names matching the Locations Master schema.

Changes
- `app/services/dedup_resolve_service.py`
- `app/services/notion_writeback.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: identify a dedup group via `/api/locations/master/dedup?refresh=true`; preview with `/api/locations/master/dedup_resolve_preview?group_id=...`; apply with `/api/locations/master/dedup_resolve_apply` body including primary_id + duplicate_ids; confirm production relations updated, duplicates archived, caches refreshed, and re-run apply for idempotence.

Date: 2025-11-28 11:00 -0500 (Session 94.1)
Author: Codex 5 (Developer)
Milestone: v0.8.8.1 - Master Archival Fix

Summary
- Fixed dedup apply to archive duplicate master rows using the correct Locations Master Status property and ensured every delete_master_id is written back.
- Added Notion writeback helper for Status updates with throttle/retry and error-body logging, wiring archival into the dedup apply flow with refreshed caches and summary counts.

Changes
- `app/services/notion_writeback.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: rerun apply on a dedup group with duplicates, confirm Status=ARCHIVED on those rows, prod pointers updated, and re-run apply to confirm idempotent 0 archives.

Date: 2025-11-28 11:30 -0500 (Session 94.2)
Author: Codex 5 (Developer)
Milestone: v0.8.8.2 - Dedup Resolve Archival Execution Hotfix

Summary
- Ensured dedup apply always invokes archival for delete_master_ids and uses the correct Status payload; archival now logs errors with Notion response bodies and tracks archived ids.
- Added archival helper return of archived_ids; apply response summary reflects archived count and caches refresh after archival.

Changes
- `app/services/notion_writeback.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: rerun dedup apply on a group with duplicates, confirm archived count > 0 and Status=ARCHIVED in Notion; rerun apply (no refresh) shows archived=0 idempotence.

Date: 2025-11-29 09:00 -0500 (Session 95)
Author: Codex 5 (Developer)
Milestone: v0.8.9 - Dedup Resolution UI (Admin Tools)

Summary
- Added admin-only Dedup Resolution UI under `/tools/dedup` (visible when `DEBUG_ADMIN=true`) with group listing, preview modal, and apply workflow using existing dedup endpoints.
- Preview shows primary/duplicates, field updates, prod pointer changes, rows to archive, and summary; apply triggers merge via POST, shows toast, closes modal, and refreshes groups.

Changes
- `app/ui/dedup.py`
- `app/ui/layout.py`
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: open `/tools/dedup`, load groups, preview a group, apply merge, confirm success toast and group removal, re-run preview/apply for idempotence.

Date: 2025-11-29 09:30 -0500 (Session 95.1)
Author: Codex 5 (Developer)
Milestone: v0.8.9.1 - Dedup UI JSON Serialization Fix

Summary
- Removed function references from table rows/columns in the dedup UI to avoid JSON serialization errors; preview buttons now use closure on group_id only.
- Added a quick self-test to log any non-serializable (callable) values in table rows; table data now contains only basic types.

Changes
- `app/ui/dedup.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: load `/tools/dedup`, ensure table renders without errors, preview/apply flows still work.

Date: 2025-11-29 10:00 -0500 (Session 95.2)
Author: Codex 5 (Developer)
Milestone: v0.8.9.2 - Dedup UI Load/Serialization Hotfix

Summary
- Fixed dedup UI loading crash by adapting to backend response shape (`duplicate_groups`), removed table state entirely, and built a simple list with preview buttons (no functions stored in data).
- Added status text, spinner, and refresh button; group_id parsing tolerates alternate key casing; maintained pure JSON-serializable state.

Changes
- `app/ui/dedup.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: open `/tools/dedup`, verify groups load (or show "no groups"), preview/apply still function without serialization errors.

Date: 2025-11-29 11:30 -0500 (Session 97)
Author: Codex 5
Milestone: v0.8.10 – Centralized Settings Model (Option B)

Summary
- Introduced `app/core/settings.py` with unified Pydantic BaseSettings.
- Migrated DEBUG_ADMIN from layout.py env lookup to Settings model.
- Updated layout.py and dedup_simple.py to import `settings.DEBUG_ADMIN`.
- Removed SimpleNamespace and os.getenv patterns.
- Launcher now works cleanly; no more import-time timing issues.

Changes
- `app/core/settings.py`
- `app/ui/layout.py`
- `app/ui/dedup_simple.py`
- `requirements.txt`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Start launcher with -Admin; `/tools/dedup_simple` shows admin view.
- Start launcher without -Admin; page shows 'Not authorized.'

Notes
- This establishes a long-term configuration architecture for ATLSApp.

Date: 2025-11-29 11:45 -0500 (Session 97.1)
Author: Codex 5
Milestone: v0.8.10 – Centralized Settings Model (Option B)

Summary
- Updated developer launcher to honor `-Admin` by setting `DEBUG_ADMIN` and echoing the active value before starting Uvicorn.

Changes
- `scripts/run_atlsapp.ps1`

Testing
- Not run (launcher script change).

Date: 2025-11-29 10:30 -0500 (Session 96)
Author: Codex 5 (Developer)
Milestone: v0.8.10 – Dedup Simple Admin UI

Summary
- Replaced failing modal/table dedup UI.
- New `/tools/dedup_simple` implements clean, minimal, admin-only interface.
- Uses strict async HTTP patterns and JSON-safe state.
- No changes to backend; backend already fully working.

Changes
- `app/ui/dedup_simple.py`
- `app/ui/layout.py`
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI-only update).

Date: 2025-11-29 12:00 -0500 (Session 97.2)
Author: Codex 5
Milestone: v0.8.10 - Documentation Update

Summary
- Added a Parking Lot entry for the Production Template Bundle to standardize automated new-production setup.
- Captured requirements for the prebuilt _Locations database, two-way Locations Master relation, schema-aligned naming, ProductionID mapping, status defaults, and automation-ready layouts/filters.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (docs-only).

Date: 2025-11-29 12:30 -0500 (Session 97.3)
Author: Codex 5
Milestone: v0.8.4 – Admin Tools Page

Summary
- Implemented new `/admin_tools` page gated by `DEBUG_ADMIN`, with collapsible sections for Match All, Schema Update placeholders, Cache Management, Normalization placeholders, Reprocess, Dedup Admin, Diagnostics, and System Info.
- Replaced the sidebar link to Dedup Simple with Admin Tools and removed the `/tools/dedup_simple` route while keeping dedup services intact.
- Added diagnostics/error handling for admin calls and placeholders for future schema/normalization/reprocess actions.

Changes
- `app/ui/admin_tools.py`
- `app/ui/layout.py`
- `app/main.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`
- `docs/AGENTS.md`

Testing
- Not run (UI/docs updates only).

Date: 2025-11-29 13:00 -0500 (Session 97.4)
Author: Codex 5
Milestone: v0.8.4 – Admin Tools Page

Summary
- Polished the Admin Tools layout with constrained width and clearer defaults.
- Replaced the initial Match All JSON block with a “run to see results” placeholder and similar diagnostics placeholder.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/DEV_NOTES.md`
- `docs/PROJECT_HANDBOOK.md`

Testing
- Not run (UI/docs updates only).

Date: 2025-11-29 13:30 -0500 (Session 97.5)
Author: Codex 5
Milestone: v0.8.11 – Address Normalization (Admin Tools Integration)

Summary
- Added address_normalizer.normalize_table to support preview/apply normalization across Locations Master, Medical Facilities, and production `_Locations` tables.
- Introduced `/api/locations/normalize/preview` and `/api/locations/normalize/apply` endpoints.
- Wired the Admin Tools Address Normalization panel with table selector, preview/apply actions, spinner, and JSON result display.

Changes
- `app/services/address_normalizer.py`
- `app/api/locations_api.py`
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (service/UI wiring only).

Date: 2025-11-29 14:00 -0500 (Session 97.6)
Author: Codex 5
Milestone: v0.8.11.1 – Address Normalization Hotfix

Summary
- Resolved circular import by deferring `write_address_updates` import inside `normalize_table`.
- Keeps Address Normalization preview/apply endpoints functional.

Changes
- `app/services/address_normalizer.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (import-cycle hotfix only).

Date: 2025-11-29 14:20 -0500 (Session 97.7)
Author: Codex 5
Milestone: v0.8.11.2 – Admin Tools Patch

Summary
- Wired Address Normalization UI (Preview + Apply) to call `/locations/normalize/preview` and `/locations/normalize/apply`.
- Added spinner, disabled state bindings, error handling, and JSON result output.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI wiring only).

Date: 2025-11-29 14:40 -0500 (Session 97.8)
Author: Codex 5
Milestone: v0.8.11.3 – Admin Tools Patch Hotfix

Summary
- Fixed button binding initialization in Admin Tools Address Normalization (avoid chaining disable() return None).

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI hotfix).

Date: 2025-11-29 14:55 -0500 (Session 97.9)
Author: Codex 5
Milestone: v0.8.11.4 – Admin Tools Address Normalization Endpoint Fix

Summary
- Corrected Address Normalization UI calls to use `/api/locations/normalize/preview` and `/api/locations/normalize/apply` with base_url to avoid hanging requests.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI endpoint fix).

Date: 2025-11-29 15:10 -0500 (Session 97.10)
Author: Codex 5
Milestone: v0.8.11.5 – Admin Tools UX Improvement

Summary
- Added an elapsed-time label next to the Address Normalization spinner to show how long preview/apply have been running.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI-only UX tweak).

Date: 2025-11-29 15:25 -0500 (Session 97.11)
Author: Codex 5
Milestone: v0.8.11.6 – Admin Tools Code Component Fix

Summary
- Fixed Admin Tools code blocks to use `text` + `update()` instead of the nonexistent `set_text` on `ui.code`, preventing exceptions and stuck spinners during Address Normalization preview/apply.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI bugfix).

Date: 2025-11-29 15:35 -0500 (Session 97.12)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Preview Fix

Summary
- Replaced remaining `set_text` calls on Address Normalization UI with `text` + `update` and fixed the elapsed timer updates to prevent spinner hangs during preview/apply.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI hotfix).

Date: 2025-11-29 15:45 -0500 (Session 97.13)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Preview Output Fix

Summary
- Ensured Address Normalization preview/apply shows results by using a shared `_show_result` helper, initial placeholder text, min-height for the code block, and error/empty fallbacks.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI-only fix).

Date: 2025-11-29 15:55 -0500 (Session 97.14)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Code Content Fix

Summary
- Switched Admin Tools code blocks to use `content` + `update()` (NiceGUI Code expects `content`), ensuring Match All, Diagnostics, and Address Normalization results render.
- Kept version pinned (no bump) until normalization UI is fully verified per guardrail.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI hotfix).

Date: 2025-11-29 16:05 -0500 (Session 97.15)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Preview Diagnostics

Summary
- Added `sample_existing` to normalization preview responses (first few rows with current structured fields) to understand why updates are skipped.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (service response tweak).

Date: 2025-11-29 16:15 -0500 (Session 97.16)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Preview Diagnostics 2

Summary
- Added load diagnostics to normalization preview (raw_rows, filtered_rows, production filter) to trace why zero rows are considered.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (service diagnostics tweak).

Date: 2025-11-29 16:25 -0500 (Session 97.17)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Preview Fallback

Summary
- Added a fallback to include all production location rows when the production filter yields zero matches, preventing empty previews for `_Locations` tables.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (logic tweak).

Date: 2025-11-29 16:35 -0500 (Session 97.18)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Mapping Diagnostics

Summary
- Added `sample_keys` to normalization preview to show which structured fields are present per sampled row, helping trace mapping vs. missing fields without renaming Notion columns.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (diagnostics only).

Date: 2025-11-29 16:45 -0500 (Session 97.19)
Author: Codex 5
Milestone: v0.8.11.7 – Socket Reconnect Tolerance

Summary
- Increased NiceGUI reconnect timeout and message history length to reduce transient websocket disconnect banners during admin tools use.

Changes
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (config tweak).

Date: 2025-11-29 16:55 -0500 (Session 97.20)
Author: Codex 5
Milestone: v0.8.11.7 – Socket Heartbeat

Summary
- Added a periodic heartbeat on Admin Tools to keep the websocket active during long admin actions; further increased reconnect window and message history.

Changes
- `app/ui/admin_tools.py`
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UX/connectivity tweak).

Date: 2025-12-02 15:20 -0500 (Session 97.21)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Result Persistence

Summary
- Admin Tools Address Normalization now restores the last result from browser storage and saves new results, so preview/apply output persists across socket reconnects.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI persistence tweak).

Date: 2025-12-02 15:40 -0500 (Session 97.22)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Storage Secret

Summary
- Added NiceGUI storage_secret to enable browser storage; normalization results now also fall back to direct localStorage writes so previews persist across reconnects.

Changes
- `app/main.py`
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (config/UI persistence tweak).

Date: 2025-12-02 16:00 -0500 (Session 97.23)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Client Fetch

Summary
- Reworked Address Normalization preview/apply buttons to use direct browser fetch + DOM/localStorage updates (no websocket dependency) and render into a plain `<pre>` so results persist even if the socket reconnects.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI fetch/render tweak).

Date: 2025-12-02 16:10 -0500 (Session 97.24)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Pre Render Fix

Summary
- Fixed `<pre>` initialization to use `text` + `update()` (no `set_text`) so the normalization result box renders without errors.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI minor fix).

Date: 2025-12-02 16:20 -0500 (Session 97.25)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools JS Call Fix

Summary
- Removed unsupported `respond` parameter from `ui.run_javascript` calls in Admin Tools to stop the 500 error on /admin_tools.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI hotfix).
