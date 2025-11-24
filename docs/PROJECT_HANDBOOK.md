# Project Handbook - ATLS GUI App  
Last Updated: 2025-11-21

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
- Dark Mode Source of Truth: Quasar/NiceGUI’s `body--dark` class is authoritative. Page header blocks must include the `atls-page-header` class so shared CSS can target them. Tailwind `dark:` variants are allowed but must rely on `body--dark`, and theme persistence is handled by monitoring this class.
- Dark Mode Architecture:
  - Quasar controls dark mode using `body--dark`.
  - Dark-mode visuals (layout, global header, page headers, tables) are handled via CSS keyed on `body--dark`; no Tailwind `.dark` class or JS toggles are used.
  - Page Header Blocks and Global Header use `atls-page-header` and `atls-global-header` for reliable dark-mode overrides.
- Dark Mode Status (v0.4.17): current dark-mode visuals remain inconsistent; feature will be revisited in a future release.

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
v1.0.0 - Production release
```

---

# 12. Collaboration Roles

- Jay — Owner  
- ChatGPT — Project Manager  
- Codex 5 — Developer  

---

# 13. Notes for Codex 5

- Avoid blocking the UI event loop  
- Use async httpx for network calls  
- Always wrap external calls with try/except  
- Keep changes modular  
- Update `DEV_NOTES.md` every session  
- Follow this Handbook and the Project Framework
