# Codex Execution Manifest — Phase 1A (Medical Only)

This manifest replaces Phase 1 for active execution.

All Asset and Production work is complete and locked.
This manifest focuses exclusively on the Medical subsystem.

---

## Global Rules

* Process specifications strictly in the order listed.
* Treat each referenced document as authoritative.
* Do NOT reinterpret, merge, or extend specifications.
* Do NOT pause for confirmation between steps.
* Do NOT add features, automation, permissions, or schema changes unless explicitly specified.
* If a specification cannot be executed as written, STOP and report the blocking issue.

---

## Execution Order

### 1. MEDICAL_SUBSYSTEM.md

* Action: Create spec and implement read-only UI
* Scope:

  * Medical list view (/medical)
  * Medical detail view (/medical/{MedicalFacilityID})
  * Read-only associations to Productions and Locations
* Constraints:

  * No editing
  * No workflows
  * No automation

### 2. MEDICAL_SUBSYSTEM_LOCK.md

* Action: Documentation only
* Condition: Execute only after Step 1 completes successfully

---

## Completion

Execution is complete when:

* Medical subsystem read-only views are implemented
* Medical subsystem is formally locked
* No speculative behavior was introduced

---

Status: Phase 1A execution manifest active
