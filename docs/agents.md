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

### Restrictions
- No schema changes without approval.
- No hard-coded URLs or secrets.
- No adding dependencies.

### PowerShell Command Behavior (Reminder)

When generating PowerShell commands, Agents must not use Unix utilities such as `sed`, `awk`, `grep`, or `cut`. Use native PowerShell equivalents only. Refer to DEV_TOOLS.md for the full rule and correct command patterns.

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

## 12. Summary
Jay sets the vision, ChatGPT architected the system and maintains quality, and Codex executes implementation cleanly.
