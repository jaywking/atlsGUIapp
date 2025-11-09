# Project Handbook – ATLS GUI App

This handbook defines the internal structure, coding standards, and operational workflow for development under VS Code + Codex 5.

---

## 1️⃣ Purpose

Transform *LocationSync* command-line scripts into a GUI-based workflow using **NiceGUI** and **FastAPI**, maintaining clear separation between:

- User interface  
- Backend automation scripts  
- External data APIs (Notion, Google Maps)

The goal: a modular, browser-based safety-management console that connects ATLS production data, location info, and medical facility lookups in real time.

---

## 2️⃣ Folder Structure

```

atlsGUIapp/
├─ app/
│   ├─ main.py              # Entry point (FastAPI + NiceGUI)
│   ├─ ui/                  # GUI pages
│   ├─ api/                 # FastAPI routers / adapters
│   └─ services/            # Shared logic (optional)
├─ scripts/                 # Original automation scripts (import-ready)
├─ docs/                    # Documentation for ChatGPT + Codex 5
├─ requirements.txt
└─ .env                     # Environment variables

```

---

## 3️⃣ File Naming & Conventions

| Category | Convention | Example |
|-----------|-------------|---------|
| UI Pages | lowercase nouns | `locations.py`, `medicalfacilities.py` |
| API Routers | `<feature>_api.py` | `locations_api.py`, `facilities_api.py` |
| Scripts | retain legacy names | `process_new_locations.py` |
| Docs | SCREAMING_SNAKE_CASE.md | `PROJECT_HANDBOOK.md` |

---

## 4️⃣ Code Style

- **Formatting:** PEP 8, 4-space indents, 88-char width.  
- **Comments:** Inline for logic, docstrings for functions.  
- **Type hints:** Include for function arguments and returns.  
- **Logging:** All API endpoints return JSON objects in the form  
  `{"status": "success|error", "message": "..."}`.  Use `/api/jobs/logs` for history and `/api/jobs/prune` to force log rotation. Configure retention with `LOG_ROTATE_DAYS` and `LOG_MAX_ENTRIES` in `.env`.  
- **Avoid print():** Return structured data instead of printing to console.  
- **UI consistency:** Use NiceGUI’s `ui.row()`, `ui.column()`, and `ui.card()` for layout.  

---

## 5️⃣ Environment & Secrets

`.env` file (never committed):

```

NOTION_TOKEN=
GOOGLE_MAPS_API_KEY=
S3_BUCKET=
S3_ENDPOINT=
APP_PASSWORD=
LOG_PATH=app/data/jobs.log
LOG_ROTATE_DAYS=7
LOG_MAX_ENTRIES=1000

```

These defaults keep the JSONL job log under control. Override per environment or via `settings.py` later.

Use `python-dotenv` or NiceGUI's config loader to access these variables safely.

Current UI modules: `productions.py` (placeholder dashboard), `locations.py`, `medicalfacilities.py`, `jobs.py`, `settings.py`, plus additional stubs as features graduate from scripts to NiceGUI.

Operational diagnostics are mirrored to `./logs/app.log` whenever the FastAPI server is running. The folder is gitignored; check it alongside the console when debugging connection tests or other backend activity.

---

## 6️⃣ Development Workflow

1. **Branching:** Create a new branch for each feature.  
2. **Coding:** Implement via Codex 5 in VS Code following this handbook.  
3. **Testing:** Run locally using `uvicorn app.main:fastapi_app --reload`.  
4. **Commit:** Write clear commit messages (`feat:`, `fix:`, `docs:`).  
5. **Document:** Update `/docs/DEV_NOTES.md` and `/docs/API_MAP.md`.  
6. **Sync:** Post summary or diffs here in ChatGPT for review.  

## 6.1 Frontend Integration

- UI buttons call backend APIs with relative paths (`/api/...`) via the helper in `app/services/api_client.py`.
- Never hard-code `http://localhost` or specific ports in UI modules; the helper derives the correct base URL from the active client so browser origin and server origin always match.

---

---

## 7️⃣ Testing Guidelines

| Area | Tool | Objective |
|------|------|------------|
| **API Endpoints** | `curl`, Postman, or browser | Confirm JSON responses, error handling |
| **UI** | Browser testing | Validate navigation, toasts, and spinners |
| **Scripts** | Python CLI | Ensure import safety and proper returns |
| **Integration** | Full run in FastAPI context | Validate end-to-end workflow |
| **Settings Diagnostics** | `/api/settings/test_connections` or Settings UI button | Verify Notion token and Google Maps key without leaving the app |
| **Jobs Maintenance** | Jobs UI "Archive Now" button (`/api/jobs/prune`) | Confirm pruning stats, filters, and archive results |

All UI-triggered tests must target relative `/api/...` routes so the browser origin matches the active FastAPI host.

---

## 7.1 Jobs Page Operations

The Jobs / Logs screen consolidates operational history. Key tools now available:

- **Filters & Search:** Category, status, and free-text filters execute client-side so reviewers can isolate specific workflows quickly.
- **Sorting + Highlighting:** Columns are sortable, the newest entries auto-scroll into view after refresh, and the five most recent entries receive a subtle background for easy spotting.
- **Auto-refresh:** Optional 10-second polling keeps the table fresh during long-running processes.
- **Archive Now:** Triggers `/api/jobs/prune` directly from the UI, displaying `{kept, archived}` counts so teams know how much history remains after each rotation.

Always validate spinner/toast feedback and the archive summary when testing Jobs UI enhancements.

---

## 8️⃣ Documentation Rules

- **Public info:** `README.md` (root)  
- **Internal structure:** `PROJECT_HANDBOOK.md`  
- **Agent definitions:** `AGENTS.md`  
- **Active log:** `DEV_NOTES.md`  
- **Endpoints:** `API_MAP.md`  
- **Versioning:** `CHANGELOG.md` (optional)

Every new API or major feature must be reflected in both `API_MAP.md` and `DEV_NOTES.md`.

---

## 9️⃣ Versioning

Use semantic versioning:
```

v0.1.0  – Prototype GUI
v0.2.0  – API integration (Locations, Facilities)
v0.3.0  – Job logging + Settings testers
v1.0.0  – Production release

```

---

## 🔟 Collaboration Roles

| Role | Agent | Description |
|------|--------|-------------|
| **Project Manager** | ChatGPT | Oversees architecture, documents, and planning. |
| **Developer** | Codex 5 (VS Code) | Implements code and updates docs. |
| **Owner** | Jay King | Approves merges, tests features, manages secrets. |

---

## 🧩 Notes for Codex 5

- Never execute long-running blocking calls directly in API routes; use async or background tasks.  
- Always catch exceptions and return structured errors.  
- Respect existing naming and folder structure.  
- Update `DEV_NOTES.md` after each completed feature.

---

## 🪶 Last Updated
2025-11-09
