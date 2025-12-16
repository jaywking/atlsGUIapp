# AGENTS.md — ATLSApp Agent Roles & Collaboration Model
Last Updated: 2025-11-21

## 1. Purpose of This Document
ATLSApp uses a hybrid human/AI development model. This file establishes:
- Roles and responsibilities for Jay, ChatGPT, and Codex 5.
- How tasks flow from idea → plan → implementation → documentation.
- Guardrails that keep the project stable and maintainable.

## 2. Agent Overview
| Agent | Role | Core Responsibilities |
|-------|------|------------------------|
| Jay (Owner) | Vision, requirements, acceptance | Defines features, approves solutions, manages priorities |
| ChatGPT | Project Manager, Systems Architect | Designs architecture, prepares prompts, reviews code, maintains documentation |
| Codex 5 | Developer | Writes and refactors code, implements UI/API/service logic |

## 3. Jay — Owner
### Primary Responsibilities
- Defines feature requirements.
- Approves solution designs.
- Reviews completed work.
- Provides domain expertise and updated documentation.

### What Jay Does Not Do
- Debug implementation details.
- Manage internal architecture.
- Handle NiceGUI or async constraints.

## 4. ChatGPT — Project Manager & Systems Architect
### Primary Duties
- Translate user goals into architecture.
- Prepare Codex-ready prompts.
- Maintain all documentation.
- Enforce guardrails: async-only HTTP, NiceGUI slot rules, relative API paths.
- Validate Codex outputs.

## 5. Codex 5 — Developer
### Primary Duties
- Implement code exactly as designed.
- Maintain async correctness.
- Preserve existing behavior.
- Log changes and run compile checks.
- Follow NiceGUI 3.2.x slot rules: `add_slot` is a context manager/template string, not a callable; define slot content inside `with table.add_slot('body-cell-...'):` (bind loop vars via default args). Do not put Python callables in `columns` because they are not JSON-serializable during initial render.
- At the start of every new session, Codex must recursively scan the full project folder structure using PowerShell commands (e.g., `Get-ChildItem -Recurse`). Codex must identify all relevant files, modules, and configurations before performing any task. Codex must never assume file locations; it must discover them.

### Restrictions
- No schema changes without approval.
- No hard-coded URLs or secrets.
- No adding dependencies.
- When using ripgrep (rg) inside PowerShell 7 (pwsh.exe), always specify directories explicitly (e.g., app/services/ or app/services/*). Avoid bare directory names like app/services, which PowerShell may interpret as literal files.
- Codex may not ask the user where files, modules, or configuration values are located unless they truly do not exist in the repository. Codex must determine project structure by scanning the filesystem at session start.

### PowerShell Command Behavior (Reminder)

`sed` is available now; it can be used when helpful. Other Unix utilities (`awk`, `grep`, `cut`) may not be present—prefer native PowerShell equivalents unless you have confirmed the tool exists. Refer to DEV_NOTES.md for the full rule and correct command patterns.

## 6. Collaboration Workflow
1. Jay provides a request.
2. ChatGPT designs the solution.
3. Codex implements.
4. ChatGPT updates documentation.
5. Jay reviews and approves.

## 7. Agent Communication Rules
- ChatGPT keeps instructions concise and structured.
- Codex follows prompt instructions exactly.
- Jay reviews outputs and provides direction.

## 8. Error Handling
- ChatGPT prepares corrective prompts.
- Codex applies corrections without architectural changes.

## 9. Documentation Responsibilities
| File | Owner | Purpose |
|------|--------|---------|
| README.md | ChatGPT | High-level summary |
| PROJECT_HANDBOOK.md | ChatGPT | Architecture + workflow |
| DEV_NOTES.md | ChatGPT & Codex | Session-by-session log |
| AGENTS.md | ChatGPT | Roles & collaboration model |

## 10. Version Governance
ChatGPT manages milestones, version naming, and roadmap updates.

## 11. Future Expansion
- Automated regression testing prompts.
- Codex linting rules.
- Schema evolution guidelines.

## 12. UI Design Heuristic (Forward-Looking)
- Prefer simpler, robust patterns when wiring UI/framework boundaries.
- Use primitive data (strings/numbers) at UI edges; avoid passing rich objects unless strictly necessary.
- Assume NiceGUI/Quasar abstractions can be leaky; design defensively and avoid complex object-binding.
- When multiple valid approaches exist, choose the one that is easiest to reason about, debug, and maintain (even if less “elegant”).
- This heuristic exists to prevent fragile UI behavior from hidden framework assumptions; it is a forward-looking guardrail, not a critique of prior work.

## 13. Schema Report Tool (Diagnostic)
- Use the Admin Tools “Generate Schema Report” action to pull a plain-text snapshot of Notion schemas; it’s for diagnosis only.
- Reports include canonical databases and all PSL tables; run it for validation errors, schema drift checks, or confirming property names/types before changing write logic.
- Run it when investigating Notion 400 validation errors, checking for schema drift across productions, or confirming property names/types before changing write logic.
- Treat reports as guidance; writes must still rely on explicit intent-based whitelists, not live schema introspection.

## 14. Global Debug Logging
ATLSApp supports an opt-in debug logging mechanism for service-level tools. Set `DEBUG_TOOLS=1` to enable append-only diagnostics written to `logs/debug_tools.log`. Logs are not automatically inspected and must be explicitly referenced when requesting debugging assistance.

## 15. Summary
Jay sets the vision, ChatGPT architected the system and maintains quality, and Codex executes implementation cleanly.
Admin Tools UI is now at `/admin_tools` and should be the target location for future maintenance and debugging tools.
