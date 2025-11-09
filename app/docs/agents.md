# AGENTS.md – ATLS GUI App

Defines the roles, communication protocols, and collaboration model for all human and AI agents working on the ATLS GUI App project.

---

## 1️⃣ Purpose

To formalize how **Jay**, **ChatGPT**, and **Codex 5** collaborate on the development of the ATLS GUI App — ensuring consistency, transparency, and continuity across tools and platforms.

The system is designed to keep ChatGPT as the *strategic project manager* and Codex 5 as the *implementation engineer* within VS Code.

---

## 2️⃣ Active Agents

| Agent | Role | Platform | Primary Function |
|--------|------|-----------|------------------|
| **Jay (Human Developer)** | Project Owner | VS Code, GitHub, ChatGPT | Provides vision, direction, testing, and final approvals. |
| **ChatGPT (Project Manager)** | AI Manager | ChatGPT | Maintains documentation, tracks progress, defines tasks, and ensures architectural consistency. |
| **Codex 5 (Developer)** | AI Engineer | VS Code (ChatGPT Extension) | Implements code, fixes issues, and updates docs according to instructions and the handbook. |

---

## 3️⃣ Agent Responsibilities

### **Jay**
- Defines objectives and approves milestones.  
- Provides credentials and context for APIs (Notion, Google Maps, S3).  
- Communicates progress between Codex 5 and ChatGPT.  
- Ensures all commits are pushed to GitHub for archival and continuity.

### **ChatGPT**
- Maintains project documentation (`PROJECT_HANDBOOK.md`, `DEV_NOTES.md`, `API_MAP.md`).  
- Reviews diffs or status updates posted from VS Code.  
- Generates structured task lists, plans, and next steps.  
- Validates architectural decisions before implementation.

### **Codex 5**
- Writes and edits Python code following PEP 8 and internal conventions.  
- Builds FastAPI endpoints and UI integrations under the existing structure.  
- Logs each coding session’s results to `/docs/DEV_NOTES.md`.  
- Reports blockers or deviations directly to ChatGPT for planning review.

---

## 4️⃣ Communication Model

| Scenario | Action | Tool / Platform |
|-----------|---------|----------------|
| New feature request | Jay → Codex 5 | VS Code |
| Structural or design clarification | Jay ↔ ChatGPT | This chat |
| Implementation log or test result | Codex 5 → `DEV_NOTES.md` | VS Code |
| Planning or milestone updates | ChatGPT → Jay | ChatGPT (this project) |

All key changes should also be committed to GitHub for record integrity.

---

## 5️⃣ Agent Prompts

### For **Codex 5**
> Implement the [feature or endpoint] according to `/docs/PROJECT_HANDBOOK.md` and `/docs/API_MAP.md`.  
> Use structured JSON responses for API endpoints and follow spinner/notification patterns from UI examples.  
> After completion, update `/docs/DEV_NOTES.md` with summary and results.

### For **ChatGPT**
> Review the latest commit or update from Codex 5.  
> Adjust documentation, roadmap, or architecture accordingly.  
> Propose next sprint tasks for continued progress.

---

## 6️⃣ Coordination Flow

1. **Jay** defines or updates a goal.  
2. **ChatGPT** converts the goal into a technical task and documentation update.  
3. **Codex 5** executes the change in VS Code, tests locally, and logs results.  
4. **Jay** reviews output and confirms results.  
5. **ChatGPT** updates the documentation and plans next sprint.

---

## 7️⃣ Rules of Engagement

- All code changes must align with `/docs/PROJECT_HANDBOOK.md`.  
- No new files or folders without ChatGPT’s confirmation (to maintain structure).  
- All new endpoints and scripts must be documented in `/docs/API_MAP.md`.  
- Dev notes should include dates, commit IDs (if applicable), and short summaries.  
- This chat serves as the **single source of truth** for the project timeline.

---

## 8️⃣ Optional / Future Agents

| Agent | Role | Description |
|--------|------|-------------|
| **Testing Agent** | QA / Validation | Runs automated endpoint and UI tests once framework stabilizes. |
| **Docs Agent** | Documentation Sync | Keeps Markdown docs and code comments in alignment. |
| **Build Agent** | Deployment | Handles packaging, Dockerization, and hosting once production-ready. |

---

## 9️⃣ Escalation Rules

If conflicts occur between Codex 5 and ChatGPT outputs:
1. **Jay** has final authority on project direction.  
2. ChatGPT must record any override decision in `/docs/DEV_NOTES.md`.  
3. Codex 5 should adjust code accordingly and re-sync documentation.

---

## 🪶 Last Updated
2025-11-09
