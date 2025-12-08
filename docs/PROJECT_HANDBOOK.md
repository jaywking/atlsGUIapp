# Project Handbook - ATLS GUI App  
Last Updated: 2025-12-02  
Version: v0.8.12.1

This handbook defines how ATLSApp is developed using NiceGUI, FastAPI, and a structured workflow.

---

This project includes several guardrails and patterns that Codex must follow at all times. The authoritative rules live in DEV_NOTES.md (“Developer Tools & Guardrails”) and throughout PROJECT_HANDBOOK.md, but this section summarizes the key constraints for fast onboarding.

Core Development Rules

UI is built with NiceGUI, and this project uses a version that does not support lambda-based reactive class bindings.
Never use .classes(lambda: …).
Always use static class strings with Tailwind utilities and dark: variants.

Do not use @ui.expose, pywebview callbacks, or JS→Python bridges. These are not supported in this runtime.

Do not introduce custom global wrapper classes (e.g., app-header, app-content). All styling must use Tailwind classes or global CSS inside layout.py.

Do not place Python callables inside table columns, slots, or NiceGUI components. NiceGUI cannot serialize them.

Theme persistence must use localStorage only. No callbacks.

Maintain the global layout structure defined in app/ui/layout.py.
Do not restructure the shell, sidebar, or header without explicit instruction.

Where Key Logic Lives

Global layout, dark mode, typography, table styling, alignment rules, theme persistence, and UI-level CSS live in:
app/ui/layout.py

Per-page content and table definitions live in the corresponding app/ui/*.py files.

All developer guardrails, Codex rules, and NiceGUI patterns live in:
docs/DEV_NOTES.md

Architecture guidelines, versioning, naming, and workflow rules live in:
docs/PROJECT_HANDBOOK.md

Versioning Expectations

Every change increments the version in:
README.md, PROJECT_HANDBOOK.md, and DEV_NOTES.md.

Add a new Session entry in DEV_NOTES.md summarizing the work.

Follow the existing v0.4.x structure for UI and layout improvements.

Never Modify

API route behavior unless specifically requested.

Background sync logic or service architecture.

Table column definitions or editing logic unless the task explicitly requires it.

What Every Codex Session Must Do

Read: PROJECT_HANDBOOK.md, DEV_NOTES.md, layout.py.

Adhere strictly to NiceGUI rules listed above.

Use static class strings + global CSS, never lambda-wrapped classes.

Apply dark-mode via dark: Tailwind utilities, global CSS overrides, and localStorage persistence only.

Ensure any UI changes remain consistent across all pages (/dashboard, /productions, /locations, /facilities, /jobs, /settings).

Update documentation (version bump + notes) as part of every change.

---

# 1. Purpose

ATLSApp consolidates LocationSync, Medical Facility tools, Notion workflows, and diagnostic utilities into a unified browser interface.

---

# 2. Folder Structure

```
atlsGUIapp/
├ app/
│  ├ main.py
│  ├ ui/
│  ├ api/
│  ├ services/
│  ├ data/
├ scripts/
├ docs/
├ .env
├ requirements.txt
```

UI, API, and service layers must remain cleanly separated.

---

# 3. File Naming & Conventions

| Category | Convention | Example |
|----------|-----------|---------|
| UI pages | lowercase nouns | productions.py |
| API routers | <feature>_api.py | settings_api.py |
| Services | descriptive modules | background_sync.py |
| Docs | SCREAMING_SNAKE_CASE | PROJECT_HANDBOOK.md |

---

# 4. Code Style

- Async-first (`async def`, `await`, `httpx`)  
- Type hints required  
- PEP 8 formatting  
- No blocking operations  
- UI must call only relative API paths  
- API responses must follow:

```
{ "status": "success" | "error", "message": "...", "data": {...} }
```

- No secrets logged or shown in UI

---

# 5. Environment & Secrets

`.env` at the repo root, loaded automatically on app startup.

Example keys:

```
NOTION_TOKEN
NOTION_LOCATIONS_DB_ID
NOTION_PRODUCTIONS_DB_ID
GOOGLE_MAPS_API_KEY
PRODUCTIONS_CACHE_PATH
LOG_PATH
PRODUCTIONS_SYNC_INTERVAL
LOG_ROTATE_DAYS
LOG_MAX_ENTRIES
```

Logs and caches must never contain secret values.

---

# 6. Development Workflow

## Step 1 - Branch  
Each feature uses its own branch.

## Step 2 - Implement  
- UI remains thin  
- Logic lives in services  
- Use async and relative paths  
- Keep code modular and testable  

## Step 3 - Test  
- Local browser test  
- `python -m compileall`  
- Manual API verification  

## Step 4 - Commit  
Semantic messages:

- feat:  
- fix:  
- refactor:  
- docs:  

## Step 5 - Document  
Add to `DEV_NOTES.md`:

- Date  
- Milestone  
- Summary  
- Changes  
- Testing  
- Notes  
- Next recommendations  

## Step 6 - Sync/Share  
Short milestone summary posted back to ChatGPT to align PM + Dev agent context.

### Starting the Dev Server via run_atlsapp.ps1
- Double-click `scripts/run_atlsapp.ps1` to launch the dev server with a guided banner.
- The script auto-detects the repo venv (`.venv`, `venv`, or any sibling directory under the repo containing `Scripts\Activate.ps1`) and activates it.
- Port 8000 is preferred; if busy, the script auto-selects the next open port up to 8010 and reports the chosen port.
- If dependencies break, reactivate the venv then run `pip install -r requirements.txt` to reinstall packages.
- To regenerate the venv, run `python -m venv .venv`, reinstall requirements, and re-run `scripts/run_atlsapp.ps1` (it will reconnect to the new activation path automatically).

---

# 7. Dashboard Overview

- Metrics: Notion + Maps + job summary  
- Local-time conversion  
- Spinners during async loads  
- `/api/dashboard/summary` is the authoritative source of system state

---

# 8. UI Conventions

- Wide tables must be wrapped in an `overflow-x-auto` container so they remain beside the sidebar and allow horizontal scroll.
- Default table text alignment is left (headers and cells) via global CSS.
- Entity ID columns (e.g., `ProductionID`) should link to a detail/edit page instead of relying on inline editing.
- When linking to authoritative sources (e.g., Notion pages), use the built-in `url` provided by the API response; do not generate or modify Notion URLs manually.
- Root layout rows should use `ui.row(no-wrap)` to prevent sidebar wrapping; sidebars should use `shrink-0`; main content should use `flex-1` with `overflow-x-auto`; sticky headers should use `sticky top-0 z-10`; optional `max-w` wrappers improve readability on very wide screens.
- All tables share a unified Material-style header row; theme toggling is global via `ui.dark_mode()`. Avoid per-page table CSS; use the global theme block to adjust header background, borders, and text for light/dark modes.
- All table styling and alignment overrides live in `app/ui/layout.py`; target Quasar utility classes (e.g., `.text-right`, `.text-center`, `justify-*`) there. Do not add per-table or per-page alignment CSS.
- Header and sidebar classes must be reactive (lambda-based) for light/dark mode; the theme toggle is reactive; theme preference must persist via localStorage; typography standard is Inter/Segoe UI/Arial at 15px.
- The page content wrapper and any page-level header sections must declare `bg-white text-slate-900 dark:bg-slate-900 dark:text-slate-200`.
- All page-level header blocks must use the unified section header style: `bg-white text-slate-900 dark:bg-slate-900 dark:text-slate-200 py-2.5 px-1 border-b border-slate-200 dark:border-slate-700`. Page titles/subtitles are omitted; only controls live in this block.
- Control bars: keep controls left-aligned with consistent gaps (gap-2), minimum height around 52px, and keep controls on one line until the viewport forces wrap.
- Table containers: wrap each table in an `overflow-x-auto` block with light vertical padding to keep spacing consistent.
- Hover/focus: use `hover:bg-slate-100 dark:hover:bg-slate-800` on buttons and links (including ProductionID/Link cells) for consistent feedback.
- New Admin Tools page (v0.8.4): replaces Dedup Simple in the sidebar, centralizes admin/debug/maintenance operations, is visible only when `DEBUG_ADMIN=true`, and uses collapsible sections for each tool.
- Address Normalization UI is retired; normalization now runs only during ingestion (imports/repair pipelines). Do not re-enable the panel.
- All ingestion paths (master, productions, facilities, dedup writebacks) must call the canonical ingestion normalizer before Notion writes: parse + structured fields + formatted/full address + Place_ID when present; no post-hoc bulk normalization.
- Notion Address Repair Tool (backend-only, headless): `scripts/repair_addresses.py` (targets: master, productions, facilities, or all). It performs in-place normalization of existing Notion rows, never deletes or recreates pages, and preserves identifiers/relations/status values.

### Notion Address Repair Tool
- Location: `scripts/repair_addresses.py`
- Purpose: In-place normalization of existing Notion address data (Locations Master, production _Locations tables, Medical Facilities) without deleting or recreating rows.
- Behavior: Reads current rows, normalizes via the canonical ingestion normalizer, and writes back only address-related fields (address lines, city/state/zip/country/county/borough, formatted/full address, Place_ID, latitude/longitude when present). ProdLocID, LocationsMasterID, relations, and Status values are preserved.
- Modes: `--target {master|productions|facilities|all}` with `--dry-run` to preview; uses job-logger format for structured logs.
- Safety: Backend-only; no UI; never imports external datasets or alters schemas/relations.
- Productions Search (v0.5.2): search is client-side only, applied against the locally cached rows; must not trigger backend fetches or modify background sync logic.
- Dark Mode Source of Truth: Quasar/NiceGUI's `body--dark` class is authoritative. Page header blocks must include the `atls-page-header` class so shared CSS can target them. Tailwind `dark:` variants are allowed but must rely on `body--dark`, and theme persistence is handled by monitoring this class.
- Dark Mode Architecture:
  - Quasar controls dark mode using `body--dark`.
  - Dark-mode visuals (layout, global header, page headers, tables) are handled via CSS keyed on `body--dark`; no Tailwind `.dark` class or JS toggles are used.
  - Page Header Blocks and Global Header use `atls-page-header` and `atls-global-header` for reliable dark-mode overrides.
- Dark Mode Status (v0.4.17): current dark-mode visuals remain inconsistent; feature will be revisited in a future release.
- Dark mode is currently unstable and deferred for a later milestone; it should not be modified unless explicitly instructed.

---

# 9. Testing Guidelines

### API  
- Validate structured JSON  
- Confirm error paths  
- Check timeouts for external services  

### UI  
- Verify all buttons  
- Ensure spinners show  
- Test Settings diagnostics with/without `.env`  

### Services  
- Background sync timing  
- Log rotation/archiving  
- Cache read/write paths  

---

# 10. Documentation Rules

- README.md — User-facing summary  
- PROJECT_HANDBOOK.md — Architecture + workflow  
- DEV_NOTES.md — Session-by-session progress  
- AGENTS.md — Team roles  
- Project Framework — Master reference  

Every new feature or endpoint must be documented.

---

# 11. Versioning

Semantic versioning:

```
v0.4.0 - Dashboard
v0.4.1 - Hardening & Env Autoload
v0.4.2 - Productions + Sync
v0.4.3 - UI Enhancements + Background Sync
v0.4.4 - Diagnostics UX Polish
v0.4.5 - Async Diagnostics Timing
v0.4.6 - Full Async Conversion
v0.4.7 - Productions Table UX & Slot Fixes
v0.4.8 - Productions Layout & UX Improvements
v0.4.9 - Productions Notion Link Integration
v0.4.10 - Global Layout Improvements
v0.4.11 - Global Theme + Material Table Styles
v0.4.12 - Final Table Header Alignment & CSS Consolidation
v0.4.13 - Dark Mode Polish, Persistent Theme, Typography
v0.4.14 - Content Wrapper & Header Dark Mode Completion
v0.4.14b - Header Dark Mode Override & Unified Page Header Blocks
v0.4.15b - Unified Dark-Mode Alignment & Theme Persistence Fix
v0.4.16 - Dark-Mode Stabilization
v0.4.17 - Dark Mode Follow-up Needed
v0.5.0 - Refactor Release: codebase cleaned and reorganized for clarity and maintainability; UI modules standardized; API and service modules consolidated and de-duplicated; no functional changes (structural quality improvements only)
v0.5.1 - UI Polish: standardized header alignment, control spacing, table padding, and hover/focus styling; no functional changes
v0.5.2 - Productions Search Fix: restored client-side search on /productions with case-insensitive filtering; no layout or backend changes
v1.0.0 - Production release
```

Versioning guardrail: keep the version at the last known-good state while fixing issues; only bump after the fix is verified to work so we avoid trails of non-working “versions.”

---

## 12. Deferred Items / Parking Lot

This section tracks known issues, architectural concerns, or improvements that must be revisited in future milestones. Items here are not part of the current milestone but require planned review.

### 12.1 Current Deferred Items

1. **Architectural redesign needed for long-running Medical Facilities fill/backfill job**  
   - v0.6.1 removes the heavy job from the GET endpoint, fixing the immediate UI timeout.  
   - However, the underlying fill/backfill process is still a synchronous, long-running operation tied to the main FastAPI worker.  
   - A future milestone should migrate this to a proper background job system (task queue, async worker, or scheduled service) with progress reporting and non-blocking execution.

2. **Argparse exit mitigation (API invoking CLI script)**  
   - The backend currently calls a CLI-style script, requiring temporary modification of `sys.argv`.  
   - Long-term fix: replace with a proper async service module and remove CLI/argparse dependencies from API flows.

3. **config.py inconsistencies and missing Notion ID handling**  
   - Some Notion database IDs required by facility scripts were missing or mismatched.  
   - A full review and alignment of config.py with the other ATLSApp config modules is needed.

4. **Drawer → Dialog fallback due to NiceGUI prop limitations**  
   - NiceGUI’s drawer props (e.g., `right=True`) were not stable, requiring fallback to a right-side dialog.  
   - Revisit once NiceGUI stabilizes drawer parameters in future releases.

5. **Scaling of Facility Sync (full data pull may exceed current architecture)**  
   - As Medical Facilities grow, the heavy fill/backfill job may need to be moved to a dedicated process with caching or incremental updates.  
   - Evaluate in a backend-focused milestone (v0.7.x or later).

6. **Responsive Layout Redesign (Replace Global max-width with Grid-Based Layout)**  
   - The current layout uses a fixed `max-w-[1600px]` container, centered with `mx-auto`, which limits width on large displays.  
   - In a future milestone, replace this with a responsive grid-based shell (e.g., `max-w-6xl md:max-w-7xl xl-max-w-none` or equivalent) to allow tables and data-heavy pages to use more screen width while preserving readability on smaller viewports.  
   - This requires a coordinated UI/UX redesign across all pages and should be scheduled once broader styling and layout updates are planned (beyond the v0.6.x cycle).

7. **Medical Facilities – Backend Search Endpoint (Server-Side Filtering)**  
   - The v0.6.x implementation uses client-side filtering after a single bulk fetch, which is appropriate for the current dataset size (~300–400 facilities).  
   - A future milestone (v0.7.x or later) should introduce a dedicated backend search endpoint (e.g., `/api/medicalfacilities/find`) supporting parameters such as `name_contains`, `address_contains`, `state`, and `facility_type`.  
   - This endpoint should use Notion `filter` and `sorts` blocks, support multi-parameter AND conditions, and may incorporate caching or background worker support for performance.  
   - This work should occur after the background job system and sync service architecture are introduced.

8. **Structured Address Fields (Split Address Into Components)**  
   - Currently, all addresses for Medical Facilities and Locations are stored in a single text field (e.g., “123 Main St, City, ST 12345”).  
   - A future milestone (v0.7.x or later) should split addresses into structured components such as Address Line 1, Address Line 2, City, State, ZIP, and optionally additional Google Place Details components.  
   - This will enable precise server-side filtering, sorting, data validation, geospatial queries, and clean integration with the planned Facility Sync service and background worker architecture.  
   - This work should occur after the backend refactor that introduces background jobs, caching, and the new search endpoint.

9. **Medical Facilities - Server-Side Search, Caching & Bulk Retrieval**  
   - A future milestone (v0.7.x or later) should introduce a dedicated backend search endpoint (e.g., `/api/medicalfacilities/find`) supporting query parameters such as `name_contains`, `address_contains`, `state`, and `facility_type` using Notion `filter` and `sorts` blocks.  
   - Implement API-level caching so the server maintains a refreshed copy of the full Medical Facilities dataset, reducing Notion round-trips and improving response times.  
   - Add support for larger page sizes or a bulk endpoint (e.g., `/api/medicalfacilities/all`) to reduce client fetches and improve bootstrap performance.  
   - These changes depend on the future background worker architecture, caching layer, and Facility Sync service, and should occur after those systems are introduced.

10. **Production Template Bundle (Automated New-Production Setup)**  
   - A future milestone should introduce a standardized Production Template Bundle that eliminates manual setup for new productions.  
   - The bundle should include:  
     - Prebuilt _Locations database with the correct schema  
     - Pre-linked relation to Locations Master, with Two-Way Relation enabled  
     - Standardized naming conventions aligned with ATLSApp schema  
     - Automatic ProductionID mapping for new production rows  
     - Default Status values consistent with v0.8.x enforcement rules  
     - Preconfigured layout, filters, and ready-to-sync structure for all automations  
   - This feature will ensure all future productions inherit a fully wired environment, eliminating repeated Notion configuration steps and guaranteeing schema consistency across all production-specific tables.

---

# 13. Collaboration Roles

- Jay - Owner  
- ChatGPT - Project Manager  
- Codex 5 - Developer  

---

# 14. Notes for Codex 5

- Avoid blocking the UI event loop  
- Use async httpx for network calls  
- Always wrap external calls with try/except  
- Keep changes modular  
- Update `DEV_NOTES.md` every session  
- Follow this Handbook and the Project Framework
