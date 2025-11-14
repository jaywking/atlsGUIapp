# Project Handbook – ATLS GUI App  
Last Updated: 2025-11-12

This handbook defines how ATLSApp is developed using NiceGUI, FastAPI, and a structured workflow.

---

# 1. Purpose

ATLSApp consolidates LocationSync, Medical Facility tools, Notion workflows, and diagnostic utilities into a unified browser interface.

---

# 2. Folder Structure

```
atlsGUIapp/
├─ app/
│  ├─ main.py
│  ├─ ui/
│  ├─ api/
│  ├─ services/
│  └─ data/
├─ scripts/
├─ docs/
├─ .env
└─ requirements.txt
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

## Step 1 — Branch  
Each feature uses its own branch.

## Step 2 — Implement  
- UI remains thin  
- Logic lives in services  
- Use async and relative paths  
- Keep code modular and testable  

## Step 3 — Test  
- Local browser test  
- `python -m compileall`  
- Manual API verification  

## Step 4 — Commit  
Semantic messages:

- feat:  
- fix:  
- refactor:  
- docs:  

## Step 5 — Document  
Add to `DEV_NOTES.md`:

- Date  
- Milestone  
- Summary  
- Changes  
- Testing  
- Notes  
- Next recommendations  

## Step 6 — Sync/Share  
Short milestone summary posted back to ChatGPT to align PM + Dev agent context.

---

# 7. Dashboard Overview

- Metrics: Notion + Maps + job summary  
- Local-time conversion  
- Spinners during async loads  
- `/api/dashboard/summary` is the authoritative source of system state

---

# 8. Testing Guidelines

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

# 9. Documentation Rules

- README.md → User-facing summary  
- PROJECT_HANDBOOK.md → Architecture + workflow  
- DEV_NOTES.md → Session-by-session progress  
- AGENTS.md → Team roles  
- Project Framework → Master reference  

Every new feature or endpoint must be documented.

---

# 10. Versioning

Semantic versioning:

```
v0.4.0 – Dashboard
v0.4.1 – Hardening & Env Autoload
v0.4.2 – Productions + Sync
v0.4.3 – UI Enhancements + Background Sync
v0.4.4 – Diagnostics UX Polish
v1.0.0 – Production release
```

---

# 11. Collaboration Roles

- Jay → Owner  
- ChatGPT → Project Manager  
- Codex 5 → Developer  

---

# 12. Notes for Codex 5

- Avoid blocking the UI event loop  
- Use async httpx for network calls  
- Always wrap external calls with try/except  
- Keep changes modular  
- Update `DEV_NOTES.md` every session  
- Follow this Handbook and the Project Framework
