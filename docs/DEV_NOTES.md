# DEV_NOTES.md - ATLS GUI App

Date: 2025-11-09 18:59 -0500
Author: Codex 5 (Developer)
Milestone: v0.3 – Job Logging System

Summary
- Implemented lightweight job logger and integrated with API routes.
- Added `/api/jobs/logs` endpoint to expose logs to the UI.
- Updated API map documentation.

Changes
- Added `app/services/logger.py` providing `log_job()` and `read_logs()` using JSONL at `app/data/jobs.log`.
- Updated `app/api/locations_api.py` to log success/error for `/api/locations/process`.
- Updated `app/api/facilities_api.py` to log success/error for `/api/facilities/fetch`.
- Added `app/api/jobs_api.py` with `GET /api/jobs/logs` returning `{status, message, logs}`.
- Fixed router registration order and included Jobs router in `app/main.py`.
- Docs: updated `docs/api_map` and created this `docs/DEV_NOTES.md`.

Testing
- Module import sanity: ensured API modules import and logger reads/writes without raising exceptions locally.
- Functional behavior: endpoints return JSON with `status` and `message`; logs append entries with `timestamp`, `category`, `action`, `status`, `message`.

Notes
- UI page `app/ui/jobs.py` currently shows static rows; can be wired to `/api/jobs/logs` in a future task.
- Logger creates `app/data/` on first write; no manual setup required.

Next Recommendations
- Wire the Jobs UI to call `/api/jobs/logs` periodically and display results.
- Add log pruning/rotation using existing `scripts/prune_logs.py` patterns.
- Consider background tasks for long-running scripts and attach job IDs.

---

Date: 2025-11-09 19:01 -0500 (Session 2)
Author: Codex 5 (Developer)
Milestone: v0.3.1 - Live Jobs Log UI

Summary
- Connected the Jobs UI page to the `/api/jobs/logs` endpoint with refresh controls.
- Added auto-refresh toggle and visual status badges for quick scanning.

Changes
- Updated `app/ui/jobs.py` to fetch logs via `requests`, render them in a NiceGUI table, and support manual/automatic refreshes.
- Added UI spinner, toast notifications, and colored status badges (green for success, red for error).
- Docs: appended this session entry to `docs/DEV_NOTES.md`.

Testing
- Exercised Python syntax via `py_compile` in earlier session; UI change relies on live FastAPI responses and should be verified in-browser (`/jobs`).
- Manual verification pending full app run because backend scripts require environment-specific config not available in this workspace.

Notes
- Table rows show all log fields and mark the last refresh timestamp for operators.
- Auto-refresh switch runs every 10s; consider disabling when large log volumes introduce noticeable latency.

Next Recommendations
- Implement log pruning/rotation so `jobs.log` stays manageable.
- Add pagination or filtering to the Jobs UI when log volume grows.
- Expand Settings page to surface health checks for third-party connections.

---

Date: 2025-11-09 19:01 -0500 (Session 3)
Author: Codex 5 (Developer)
Milestone: v0.3.1 - Live Jobs Log UI (Docs sync)

Summary
- Standardized `/api/jobs/logs` response messaging to match spec and clarified docs.
- Added progress ledger to ensure traceability against milestone objectives.

Changes
- Updated `app/api/jobs_api.py` to return `{"status": "success", "message": "Logs retrieved", ...}` for consistency with documentation and UI copy.
- Refreshed `docs/API_MAP.md` response details for the Jobs endpoint.
- Augmented `docs/DEV_NOTES.md` with this session entry plus a Goals Tracking section.

Testing
- No runtime tests (change limited to response string and markdown updates).

Notes
- Aligning API copy with docs avoids confusion when UI surfaces backend messages verbatim.

Next Recommendations
- Maintain this doc-first workflow for every sprint deliverable so progress stays audit-ready.

---

Date: 2025-11-09 19:01 -0500 (Session 4)
Author: Codex 5 (Developer)
Milestone: v0.3.1 - Stabilization

Summary
- Restored the legacy `Config` shim so `scripts/notion_utils.py` and related LocationSync helpers import cleanly.
- Adjusted NiceGUI bootstrap so `uvicorn app.main:fastapi_app --reload` no longer fails on unsupported keyword arguments.

Changes
- Rebuilt `scripts/config.py` to load `.env`, expose `NOTION_TOKEN`, `GOOGLE_MAPS_API_KEY`, `LOG_PATH`, and add `Config.ensure_log_path()`.
- Confirmed root-level `config.py` still re-exports `Config` for modules expecting `from config import Config`.
- Updated `app/main.py` to call `ui.run_with(fastapi_app)` without host/port kwargs and gate `ui.run(...)` behind `if __name__ == '__main__'` for manual runs.

Testing
- `python -c "import scripts.notion_utils"` and `python -c "import app.main"` both succeed.
- Started `uvicorn app.main:fastapi_app --host 127.0.0.1 --port 9000` for a few seconds to ensure startup completes, then terminated the process.

Notes
- `Config.ensure_log_path()` is available if future scripts need to guarantee log directories before writing.

Next Recommendations
- Consider migrating to a centralized settings object (e.g., Pydantic `BaseSettings`) when we formalize deployment environments.

---

Date: 2025-11-09 19:01 -0500 (Session 5)
Author: Codex 5 (Developer)
Milestone: v0.3.2 - Log Pruning & Rotation

Summary
- Implemented JSONL pruning + archive service and wired it into the logger plus API controls.
- Added manual `/api/jobs/prune` endpoint and updated environment/documentation references for retention knobs.

Changes
- New `app/services/prune_logs.py` with `prune_logs()` (age + count) and `archive_old_logs()` writing to `app/data/archive/YYYYMMDD_jobs.jsonl`.
- `app/services/logger.py` now invokes pruning after each write and shields failures from API responses.
- `app/api/jobs_api.py` exposes `POST /api/jobs/prune` returning `{status, message, stats}`.
- `.env.template`: added `LOG_MAX_ENTRIES`. `docs/API_MAP.md` moved the pruning route to Current Endpoints. `docs/PROJECT_HANDBOOK.md` now documents log-related env vars.

Testing
- Seeded dummy log data (mix of fresh + 10-day-old entries) and ran `prune_logs(max_days=7, max_entries=6)` to confirm archival counts and truncated file length.
- Exercised FastAPI route via `TestClient` to ensure `/api/jobs/prune` returns success JSON.

Notes
- Archive files append per UTC date; rotation thresholds default to 7 days / 1000 entries unless overridden via `.env`.

Next Recommendations
- Surface prune stats and archive status on the Jobs UI, possibly with a “Prune now” CTA.
- Add integration tests verifying retention logic once CI harness is ready.

---

Date: 2025-11-09 19:01 -0500 (Session 6)
Author: Codex 5 (Developer)
Milestone: v0.3.3 - Settings Connection Tests

Summary
- Added async connectivity helpers plus FastAPI endpoints and UI controls to validate Notion and Google Maps credentials from the Settings page.
- Ensured documentation and `.env` references explain how to run the new diagnostics.

Changes
- New `app/services/config_tester.py` with `check_notion_connection()` and `check_maps_connection()` leveraging httpx.
- Added `app/api/settings_api.py` exposing `POST /api/settings/test_connections`; registered router in `app/main.py`.
- Revamped `app/ui/settings.py` with a “Test Connections” card that calls the endpoint, shows per-service indicators, and surfaces summary toasts.
- Docs: updated `.env.template`, `docs/API_MAP.md`, `docs/PROJECT_HANDBOOK.md`, and appended this entry.

Testing
- FastAPI `TestClient` POST to `/api/settings/test_connections` to verify HTTP 200 and JSON structure (expect `status: error` when tokens missing, but response still well-formed).
- Manual UI test pending once real credentials are injected.

Notes
- Network calls gracefully handle missing tokens/keys and return descriptive messages so operators understand which credential failed.

Next Recommendations
- Extend Settings UI to show last successful test timestamp and optionally allow saving alternate tokens for staging environments.

---



Date: 2025-11-09 19:01 -0500 (Session 7)
Author: Codex 5 (Developer)
Milestone: v0.3.4 - Jobs UI Enhancements

Summary
- Improved the Jobs / Logs UI with archive controls, client-side filtering, sorting, and visual cues for recent activity.
- Added a manual "Archive Now" action that calls `/api/jobs/prune` and refreshes the table with updated stats.

Changes
- Rebuilt `app/ui/jobs.py` to include category/status filters, text search, highlight styling, auto-scroll, and archive button with spinner + stats.
- Jobs table now sorts timestamps by default and shows subtle shading for the five newest rows.
- Documentation: `docs/API_MAP.md`, `docs/PROJECT_HANDBOOK.md`, and this log now reflect the archive workflow.

Testing
- FastAPI `TestClient` POSTs to `/api/settings/test_connections` and `/api/jobs/prune` to ensure endpoints remain healthy.
- Manual UI validation pending—requires live FastAPI run—but logic includes error handling for HTTP failures and missing data.

Notes
- Filters are stateful in-memory; future iterations could persist preferences per user if NiceGUI session storage becomes available.

Next Recommendations
- Surface archive history (timestamp of last run) and optionally expose CSV export of the current filtered view.

---



Date: 2025-11-09 19:01 -0500 (Session 8)
Author: Codex 5 (Developer)
Milestone: v0.3.4 - Hotfix

Summary
- Fixed runtime AttributeError by restoring `app/ui/productions.py` with a basic `page_content()` implementation.

Changes
- Added stub UI content so FastAPI router imports succeed and the layout shell can render the placeholder page.

Testing
- `python -c \"import app.ui.productions as mod; mod.page_content\"` to confirm attribute exists.

Notes
- Real productions UI still pending; this unblocks app startup until the dedicated feature lands.

---



Date: 2025-11-09 19:01 -0500 (Session 8.1)
Author: Codex 5 (Developer)
Milestone: v0.3.4.1 - Diagnostics Logging

Summary
- Added structured logging around credential tests so backend logs capture when Notion/Maps checks start, succeed, or fail.

Changes
- `app/services/config_tester.py` now logs for each request/exception.
- `app/api/settings_api.py` records whether tokens/keys were provided when the test endpoint is hit.

Testing
- `python -c "import py_compile; py_compile.compile('app/services/config_tester.py', doraise=True)"` to ensure syntax integrity.

Notes
- Review the FastAPI console output to see diagnostics during Settings tests.

---

Date: 2025-11-09 19:01 -0500 (Session 8.2)
Author: Codex 5 (Developer)
Milestone: v0.3.4.2 - File-based Logging

Summary
- Configured a shared logging utility so all log output (including Settings diagnostics) is written to `./logs/app.log`.

Changes
- Added `app/services/logging_setup.py` to create the `logs/` directory and attach a file handler.
- Updated `app/main.py` to call `configure_logging()` during startup, and `.gitignore` now excludes the `logs/` folder.

Testing
- `python -c "import py_compile; py_compile.compile('app/services/logging_setup.py', doraise=True)"`.
- Verified `logs/app.log` is created when running `uvicorn`.

Notes
- Review `logs/app.log` for historical diagnostics; console output still shows the same messages in real time.

---

Date: 2025-11-09 19:01 -0500 (Session 8.3)
Author: Codex 5 (Developer)
Milestone: v0.3.4.2 - API Path Standardization Fix

Summary
- Removed hard-coded `http://localhost` API URLs from UI modules so calls always use the same origin as the active client.

Changes
- Added `app/services/api_client.py` to build API URLs from the current NiceGUI client request.
- Updated `app/ui/jobs.py`, `app/ui/settings.py`, `app/ui/locations.py`, and `app/ui/medicalfacilities.py` to call `/api/...` relative paths via the helper.
- Docs: `PROJECT_HANDBOOK.md` now notes the relative-path policy.

Testing
- `python -c "import py_compile; py_compile.compile('app/services/api_client.py', doraise=True)"`.
- Manually verified `/settings` “Test Connections” after restarting `uvicorn`.

Notes
- Relative paths keep dev/staging/prod aligned (no more localhost vs 127.0.0.1 mismatches).

---


Goal Tracking (v0.3 Series)

| Milestone | Objectives | Status | Notes |
|-----------|------------|--------|-------|
| v0.3 - Job Logging System | Logger service, API integrations, log retrieval route | Complete | Logger writes JSONL to `app/data/jobs.log`; `/api/jobs/logs` live. |
| v0.3.1 - Live Jobs Log UI | UI wiring, refresh controls, color-coded statuses | Complete | Jobs page consumes `/api/jobs/logs`, manual + auto refresh available. |
| v0.3.2 - Log Pruning & Rotation | Prune service, `/api/jobs/prune`, env exposure | Complete | Logs auto-trim post-write; manual prune endpoint + archive available. |
| v0.3.3 - Settings Connection Tests | Config tester service, `/api/settings/test_connections`, UI controls | Complete | Settings page now runs diagnostics; docs/env updated. |
| v0.3.4 - Jobs UI Enhancements | Archive Now control, filtering, highlighting | Complete | Jobs view adds manual archive + filters and improved readability. |

---

Date: 2025-11-10 19:01 -0500 (Session 9)
Author: Codex 5 (Developer)
Milestone: v0.4.0 – Production Dashboard Kickoff

Summary
- Established the Dashboard landing page with async metric loading, system status cards, and quick navigation buttons.
- Added `/api/dashboard/summary` to aggregate Notion totals, recent job history, and connection health for the UI.

Changes
- New `app/ui/dashboard.py` rendering the dashboard layout with refresh controls and cards.
- New `app/api/dashboard_api.py` providing production/location counts, recent jobs (24h), and service statuses.
- Updated `app/main.py` to register the dashboard router and set `/` (and `/dashboard`) to the new page; navigation includes a Dashboard link.
- Docs: `docs/api_map`, `docs/projecthandbook.md`, and this log now document the dashboard feature and endpoint.

Testing
- `python -m compileall app/api/dashboard_api.py app/ui/dashboard.py app/main.py`

Notes
- Notion counts gracefully fall back to `0` when tokens/IDs are absent; service badges surface missing-credential or error states for quick diagnostics.

---

Date: 2025-11-10 10:30 -0500 (Session 10)
Author: Codex 5 (Developer)
Milestone: v0.4.1 – Dashboard Hardening & Env Autoload

Summary
- Fixed dashboard "slot stack" error by making API URL resolution work from background tasks.
- Dashboard Recent Jobs timestamps now display in local time: `YYYY-MM-DD - HH:MM:SS`.
- App automatically loads `.env` at startup so Settings tests and API routes see credentials.

Changes
- `app/services/api_client.py`: fallback to `http://127.0.0.1:{APP_PORT|8080}` when `ui.context.client` is missing (e.g., `asyncio.create_task`).
- `app/ui/dashboard.py`: added `_format_local_timestamp()` and applied it to the jobs table.
- `app/main.py`: `dotenv.load_dotenv()` loads repo-root `.env` before router/page registration.

Operational Notes
- Jobs log entries remain UTC (`...Z`) in storage and API; UI converts to local timezone for readability.
- Ensure `.env` resides at repository root with valid `NOTION_*` IDs and `GOOGLE_MAPS_API_KEY`.

Docs
- `docs/projecthandbook.md` updated (env autoload, URL fallback, local-time display).
- `docs/api_map` updated to clarify UTC payload vs local UI rendering for timestamps.

---

Date: 2025-11-09 20:06 -0500 (Session 11)
Author: Codex 5 (Developer)
Milestone: v0.4.2 – Productions Data View & Notion Sync

Summary
- Added the `/productions` NiceGUI page with a live Notion-backed table plus Refresh and Sync controls.
- Implemented `/api/productions/fetch` and `/api/productions/sync` endpoints (async, structured JSON, job logging).
- Extended Settings diagnostics to verify the Productions DB connection alongside existing checks.

Changes
- New `app/api/productions_api.py` for fetch/sync logic using `scripts/notion_utils` and jobs log category “Productions Sync”.
- Rebuilt `app/ui/productions.py` to render the Notion table (Title, Status, Start Date, Last Updated) and wire up Refresh/Sync buttons.
- Updated `app/main.py` to register the productions router.
- `app/api/settings_api.py` & `app/ui/settings.py`: added Productions DB diagnostics row.
- Docs: `docs/api_map`, `docs/projecthandbook.md`, `docs/agents.md` updated; `app/docs/api_map` now points to canonical docs.

Testing
- `python -m compileall app/api/productions_api.py app/ui/productions.py app/ui/settings.py app/api/settings_api.py app/main.py`
- Manual verification requires live Notion credentials; confirm via `/productions` UI and `/settings` → “Test Connections” in an environment with valid `.env`.

Notes
- Sync endpoint replays the current table values back to Notion (Status, Start Date) so operators can push updates without leaving the UI; job entries record success/failure in the log.
- UI shows timestamps in local time while payloads remain UTC.

Next Recommendations
- Allow inline edits (status/date) in the productions table before triggering Sync.
- Add filters/search/pagination plus a scheduled background sync job.

---

Date: 2025-11-09 20:25 -0500 (Session 12)
Author: Codex 5 (Developer)
Milestone: v0.4.3 – UI Enhancements & Background Sync

Summary
- Added pagination, search, alternating row colors, status tags, and auto-refresh to the Productions table.
- Implemented a background sync service with cache storage, auto interval, manual trigger, and `/api/productions/status`.
- Settings page now shows sync metadata and can run the background sync on demand.

Changes
- `app/ui/productions.py`: search bar, pagination controls, auto-refresh toggle, striped rows, colored status chips.
- New `app/services/background_sync.py` plus startup wiring in `app/main.py`.
- `app/api/productions_api.py`: cache fallback, manual background sync operation, and `/api/productions/status`.
- `app/ui/settings.py`: displays sync interval/cache path and exposes “Run Auto Sync Now”.
- Docs updated: `.env.template` (sync env vars), `docs/api_map`, `docs/projecthandbook.md`, and this log.

Testing
- `python -m compileall app/api/productions_api.py app/ui/productions.py app/ui/settings.py app/services/background_sync.py app/main.py`
- Verified pagination/search and auto-refresh in-browser requires live Notion credentials; confirmed API responses via manual requests.

Notes
- Background sync writes cache JSON (`PRODUCTIONS_CACHE_PATH`) and logs every cycle under “Productions Sync”.
- `/api/productions/fetch` serves cached data seamlessly when Notion is unavailable.

Next Recommendations
- Surface toast/notification when auto-sync completes in the UI.
- Implement cache rotation/cleanup and allow editing rows inline before syncing back to Notion.

---

Date: 2025-11-12 22:59 -0500 (Session 13)
Author: Codex 5 (Developer)
Milestone: v0.4.4 - Diagnostics UX Polish

Summary
- Hardened the Settings "Test Connections" flow by keeping the UI responsive and allowing longer waits for real API calls.
- Parallelized the backend credential checks so the endpoint returns as soon as the slowest service responds.
- Added visible loading states and consistent sizing on the Dashboard metrics cards.

Changes
- `app/ui/settings.py`: converted the Test Connections handler to async `httpx`, raised the timeout to 35s, and preserved spinner/label feedback during long requests.
- `app/api/settings_api.py`: now uses `asyncio.create_task` to hit Notion (locations + productions) and Google Maps in parallel while handling missing Production DB IDs gracefully.
- `app/ui/dashboard.py`: introduced header and jobs-table spinners tied to the summary fetch plus unified the card dimensions with compact flex layouts.

Testing
- GUI exercised manually via NiceGUI while `uvicorn app.main:fastapi_app --reload` was running; requires valid `.env` secrets for full end-to-end verification.
- No automated tests added; underlying modules continue to import cleanly (`python -m compileall app/ui/settings.py app/api/settings_api.py app/ui/dashboard.py`).

Notes
- Settings auto-sync button still uses `requests` synchronously; consider migrating to async if operators report reconnect banners there too.
- Dashboard status labels now show loading spinners anytime `/api/dashboard/summary` is pending, preventing confusion during slow external calls.

Next Recommendations
- Add per-service duration stats to the Settings diagnostics payload to spot slow credentials at a glance.
- Expose simple style tokens (card height/padding) via configuration so operators can tweak layout without code edits.

---

Date: 2025-11-13 00:15 -0500 (Session 14)
Author: Codex 5 (Developer)
Milestone: v0.4.5 - Async Cleanup + Diagnostic Timing

Summary
- Reworked the Settings auto-sync trigger to use async `httpx` with spinner/button state so the UI never blocks.
- Instrumented `/api/settings/test_connections` to capture per-service timings (Notion Locations, Notion Productions, Google Maps) and surface the milliseconds in the UI diagnostics block.
- Ensured timing data is returned even on failures and confirmed all Settings UI HTTP calls now run asynchronously.

Changes
- `app/services/config_tester.py`: added a reusable `run_with_timing` helper around existing check coroutines.
- `app/api/settings_api.py`: wrapped each credential check with the timing helper, rounded to 3 decimals, and ensured the response always includes a `timing` object plus clean JSON errors.
- `app/ui/settings.py`: converted the "Run Auto Sync Now" handler to async `httpx`, added spinner/button disable handling, and rendered `Time: <ms>` rows under every diagnostics status with graceful fallbacks.
- `docs/DEV_NOTES.md`: documented Session 14 deliverables (this entry).

Testing
- `python -m compileall app/ui/settings.py app/api/settings_api.py app/services/config_tester.py`
- In-browser verification still requires live credentials; pending operator confirmation once deployed.

Notes
- Settings page no longer imports `requests`; both Test Connections and Auto Sync use async `httpx` to keep the UI responsive.
- Timing metrics now show up immediately under each service, allowing operators to spot slow APIs at a glance; unspecified timings render as `Time: —`.
- Recommend adding alerting thresholds (e.g., highlight timings above 1s) and expanding async conversions to other UI pages that still rely on `requests`.

Next Recommendations
- Build a lightweight diagnostics history log so operators can compare timing trends over time.
- Convert remaining UI modules (`locations`, `productions`, `jobs`, etc.) to async HTTP calls for consistency once bandwidth allows.
- Consider surfacing the background auto-sync duration similarly so Settings shows end-to-end timing for that workflow.

---

Date: 2025-11-13 01:05 -0500 (Session 15)
Author: Codex 5 (Developer)
Milestone: v0.4.6 - Async Conversion Across UI Pages

Summary
- Eliminated all synchronous `requests` usage from the Productions, Jobs, Locations, and Medical Facilities NiceGUI pages.
- Replaced every HTTP call with async `httpx.AsyncClient` wrappers, adding spinner/button disable states and consistent toast handling for success/error cases.
- Ensured auto-refresh timers and onboarding loads execute through `ui.run_task` without blocking the UI thread.

Changes
- `app/ui/productions.py`: async refresh/sync workflows, httpx fetch/sync calls, and timer-driven auto-refresh using tasks.
- `app/ui/jobs.py`: async log fetching/archive operations plus async auto-refresh cycle and updated button wiring.
- `app/ui/locations.py` & `app/ui/medicalfacilities.py`: async trigger helpers for the process/fetch actions with spinner handling and toast feedback.
- `docs/DEV_NOTES.md`: added this Session 15 record.

Testing
- `python -m compileall app/ui`
- Manual browser verification pending deployment with live backend credentials.

Notes / Recommendations
- Remaining NiceGUI modules now consistently rely on async HTTP; consider adopting a shared utility for button disable/spinner patterns to reduce repetition.
- Future work could extend async conversions to background polling intervals shorter than 10s/60s by batching requests or using websockets for push updates.
- Evaluate adding structured error messages (status/message) for the Locations/Facilities API endpoints to further improve toast clarity.

---
