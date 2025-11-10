# AGENTS.md - ATLS GUI App
Last Updated: 2025-11-09 20:06 -05:00

Defines the roles, communication protocols, and collaboration model for all human and AI agents working on the ATLS GUI App project.

---

## 1?? Purpose

Clarify how Jay, ChatGPT, and Codex 5 work together so changes ship quickly and consistently.

---

## 2?? Active Agents

| Agent | Role | Platform | Primary Function |
|--------|------|----------|------------------|
| Jay (Human Developer) | Project Owner | VS Code, GitHub, ChatGPT | Vision, direction, testing, approvals |
| ChatGPT (Project Manager) | AI Manager | ChatGPT | Docs, planning, reviews, architecture |
| Codex 5 (Developer) | AI Engineer | VS Code | Code changes, fixes, doc sync |

---

## 3?? Agent Responsibilities

### Jay
- Define objectives and approve milestones.
- Provide credentials for APIs (Notion, Google Maps, S3).
- Ensure commits are pushed to GitHub for continuity.

### ChatGPT
- Maintain project documentation in `docs/`.
- Review diffs and progress; propose next steps.
- Validate architectural decisions before implementation.

### Codex 5
- Write/edit Python, FastAPI routers, and NiceGUI UI.
- Keep endpoints returning structured JSON.
- Log each session’s results to `docs/DEV_NOTES.md`.

---

## 4?? Communication Model

| Scenario | Action | Tool |
|----------|--------|------|
| New feature request | Jay → Codex 5 | VS Code |
| Design clarification | Jay ↔ ChatGPT | This chat |
| Implementation log | Codex 5 → `DEV_NOTES.md` | VS Code |
| Planning updates | ChatGPT → Jay | ChatGPT |

All key changes should also be committed to GitHub for record integrity.

---

## 5?? Agent Prompts

### For Codex 5
> Implement the feature per `docs/projecthandbook.md` and `docs/api_map`.
> Return structured JSON from APIs; use spinner/toast patterns in UI.
> Update `docs/DEV_NOTES.md` after completion.

### For ChatGPT
> Review latest changes, adjust docs/roadmap, and propose next sprint steps.

---

## 6?? Coordination Flow

1. Jay defines or updates a goal.
2. ChatGPT converts it into tasks and doc updates.
3. Codex 5 implements, tests, and logs results.
4. Jay reviews output and confirms.
5. ChatGPT updates documentation and plans next sprint.

---

## 7?? Rules of Engagement

- Align code with `docs/projecthandbook.md`.
- Document every new endpoint in `docs/api_map`.
- Keep `docs/DEV_NOTES.md` updated with dates and summaries.
- This chat serves as the single source of truth for the project timeline.

---

## 8?? Optional / Future Agents

| Agent | Role | Description |
|-------|------|-------------|
| Testing Agent | QA / Validation | Runs automated API/UI tests when framework stabilizes |
| Docs Agent | Documentation Sync | Keeps Markdown docs and code comments aligned |
| Build Agent | Deployment | Packaging, Dockerization, hosting when production-ready |

---

## 9?? Escalation Rules

If conflicts occur between Codex 5 and ChatGPT outputs:
1. Jay has final authority on direction.
2. ChatGPT records any override decision in `docs/DEV_NOTES.md`.
3. Codex 5 adjusts code accordingly and re-syncs documentation.

---

## 10?? Speed & Editing Conventions (for Agents)

To keep iteration fast and avoid tooling hiccups:

- Shell environment: this workspace uses PowerShell on Windows. Avoid `sed`/`awk`; use `rg` for search and `Get-Content -First/-Tail` for reads.
- File edits: use the `apply_patch` tool for modifications; avoid shell editors.
- Large files: read in chunks (<= 250 lines) to prevent truncation and keep output responsive.
- Docs source of truth: prefer `docs/` as canonical documentation. If mirrored files exist under `app/docs/`, update both or keep the app copy minimal and consistent.
- Stable anchors: when adding sections to docs, maintain headers like `## 6.1 Frontend Integration`, `## 6.2 Dashboard Overview`, and `## ?? Last Updated` so patches can target reliably.
- Timestamps policy: APIs return UTC (`...Z`); UI should render local time. Reflect this in docs when changing dashboard/jobs features.
- Env loading: `.env` lives at repo root and is auto-loaded by `app/main.py`. Avoid duplicating env in other repos/paths.

These conventions reduce failed patch attempts and speed up doc sync.

---



