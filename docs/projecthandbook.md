# Project Handbook - ATLS GUI App
Last Updated: 2025-11-09 20:06 -05:00

This handbook defines the internal structure, coding standards, and operational workflow for development under VS Code + Codex 5.

---

## 1?? Purpose

Transform LocationSync command-line scripts into a GUI-based workflow using NiceGUI and FastAPI, maintaining clear separation between:

- User interface
- Backend automation scripts
- External data APIs (Notion, Google Maps)

The goal: a modular, browser-based safety-management console that connects ATLS production data, location info, and medical facility lookups in real time.

---

## 2?? Folder Structure

```
atlsGUIapp/
├─ app/
│  ├─ main.py              # Entry point (FastAPI + NiceGUI)
│  ├─ ui/                  # GUI pages
│  ├─ api/                 # FastAPI routers / adapters
│  └─ services/            # Shared logic
├─ scripts/                # Original automation scripts (import-ready)
├─ docs/                   # Documentation
├─ requirements.txt
└─ .env                    # Environment variables
```

---

## 3?? File Naming & Conventions

| Category | Convention | Example |
|-----------|-------------|---------|
| UI Pages | lowercase nouns | `locations.py`, `medicalfacilities.py` |
| API Routers | `<feature>_api.py` | `locations_api.py`, `facilities_api.py` |
| Scripts | retain legacy names | `process_new_locations.py` |
| Docs | SCREAMING_SNAKE_CASE.md | `PROJECT_HANDBOOK.md` |

---

## 4?? Code Style

- Formatting: PEP 8, 4-space indents, ~88-char width.
- Comments: Inline for logic, docstrings for functions.
- Type hints: Include for function arguments and returns.
- Logging: All API endpoints return JSON objects of the form `{"status": "success|error", "message": "..."}`. Use `/api/jobs/logs` for history and `/api/jobs/prune` to force log rotation. Configure retention with `LOG_ROTATE_DAYS` and `LOG_MAX_ENTRIES` in `.env`.
- Avoid print(): Return structured data instead of printing to console.
- UI consistency: Use NiceGUI `ui.row()`, `ui.column()`, and `ui.card()` for layout.

---

## 5?? Environment & Secrets

`.env` file (never committed):

```
APP_ENV=development
APP_PORT=8080
NOTION_TOKEN=
NOTION_PRODUCTIONS_DB_ID=
NOTION_LOCATIONS_DB_ID=
GOOGLE_MAPS_API_KEY=
LOG_PATH=app/data/jobs.log
LOG_ROTATE_DAYS=7
LOG_MAX_ENTRIES=1000
```

These defaults keep the JSONL job log under control. Override per environment or via `settings.py` later.

Environment loading
- The app automatically loads a repo‑root `.env` at startup (`app/main.py` via `python-dotenv`).
- Keep `.env` at the project root (`atlsGUIapp/.env`) so both API routes and the Settings page can read credentials.

Operational diagnostics are mirrored to `./logs/app.log` whenever the FastAPI server is running. The folder is gitignored; check it alongside the console when debugging connection tests or other backend activity.

---

## 6?? Development Workflow

1. Branching: Create a new branch for each feature.
2. Coding: Implement via Codex 5 in VS Code following this handbook.
3. Testing: Run locally using `uvicorn app.main:fastapi_app --reload`.
4. Commit: Write clear commit messages (`feat:`, `fix:`, `docs:`).
5. Document: Update `docs/DEV_NOTES.md` and `docs/api_map`.
6. Sync: Post summary or diffs here in ChatGPT for review.

## 6.1 Frontend Integration

- UI buttons call backend APIs with relative paths (`/api/...`) via the helper in `app/services/api_client.py`.
- Never hard-code `http://localhost` or specific ports; the helper derives the correct base URL from the active client so browser origin and server origin always match.
- Background tasks: when no NiceGUI client context is present (e.g., `asyncio.create_task`), the helper falls back to `http://127.0.0.1:{APP_PORT|8080}`.

## 6.2 Dashboard Overview

- Landing: `/` renders `app/ui/dashboard.py` via `layout.shell()`.
- Data Source: `/api/dashboard/summary` aggregates Notion counts, recent Jobs, and connection health.
- Navigation Hub: Quick buttons route to Productions, Locations, Jobs, Settings.
- Refresh: Metrics load asynchronously and can be refreshed without blocking the UI.
- Timestamps: Recent Jobs show local time (`YYYY-MM-DD - HH:MM:SS`). The API/log file keep UTC (`...Z`).

---

## 7?? Testing Guidelines

| Area | Tool | Objective |
|------|------|-----------|
| API Endpoints | curl, Postman, or browser | Confirm JSON responses, error handling |
| UI | Browser testing | Validate navigation, toasts, and spinners |
| Scripts | Python CLI | Ensure import safety and proper returns |
| Integration | Full run in FastAPI context | Validate end-to-end workflow |
| Settings Diagnostics | `/api/settings/test_connections` or Settings UI button | Verify Notion token and Google Maps key |
| Jobs Maintenance | Jobs UI "Archive Now" (`/api/jobs/prune`) | Confirm pruning stats and archive results |

All UI-triggered tests must target relative `/api/...` routes so the browser origin matches the active FastAPI host.

---

## 7.1 Jobs Page Operations

The Jobs / Logs screen consolidates operational history. Key tools now available:

- Filters & Search: Category, status, and free-text filters execute client-side.
- Sorting + Highlighting: Sortable columns, auto-scroll to newest, subtle highlight for last 5 entries.
- Auto-refresh: Optional 10-second polling.
- Archive Now: Triggers `/api/jobs/prune` and shows `{kept, archived}` counts.

---

## 8?? Documentation Rules

- Public info: `README.md` (root)
- Internal structure: `PROJECT_HANDBOOK.md`
- Agent definitions: `AGENTS.md`
- Active log: `DEV_NOTES.md`
- Endpoints: `api_map`
- Versioning: `CHANGELOG.md` (optional)

Every new API or major feature must be reflected in both `api_map` and `DEV_NOTES.md`.

---

## 9?? Versioning

Use semantic versioning:

```
v0.1.0  - Prototype GUI
v0.2.0  - API integration (Locations, Facilities)
v0.3.0  - Job logging + Settings testers
v0.4.0  - Dashboard landing
v0.4.1  - Dashboard hardening & .env autoload
v0.4.2  - Productions data view & Notion sync
v1.0.0  - Production release
```

---

## ?? Collaboration Roles

| Role | Agent | Description |
|------|--------|-------------|
| Project Manager | ChatGPT | Oversees architecture, documents, and planning. |
| Developer | Codex 5 (VS Code) | Implements code and updates docs. |
| Owner | Jay King | Approves merges, tests features, manages secrets. |

---

## ?? Notes for Codex 5

- Avoid long-running blocking calls in API routes; prefer async/background tasks.
- Always catch exceptions and return structured errors.
- Respect naming and folder structure.
- Update `DEV_NOTES.md` after each completed feature.

---

