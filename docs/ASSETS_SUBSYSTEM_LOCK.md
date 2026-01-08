# Assets Subsystem — Lock & Readiness Specification (v1)

## 1. Purpose

This document formally declares the Assets subsystem complete for v1 and defines what is locked, what is in scope, and what is explicitly out of scope.

Any future work that violates this document requires reopening the subsystem with a new specification.

---

## 2. Scope Covered (Locked)

The following components are implemented and locked:

### Data Model
- Assets table
- Asset ID prefixes and semantics:
  - PIC### (Photo Assets)
  - AST### (Generic Assets)
  - FOL### (Folder Assets)
- Required and optional fields as defined in ASSETS_MODEL.md

### Creation & Registration
- Photo promotion flow (PIC###)
- Folder registration flow (FOL###)
- Generic asset handling (AST###)

### Editing
- Explicit Asset Editing Flow
- Immutable vs editable fields enforced
- Hero designation excluded from editing

### Hero Handling
- Explicit Hero Photo Admin Flow
- Defensive detection of multiple heroes

### Diagnostics
- Light Asset Validation & Diagnostics
- INFO / CHECK / WARNING only
- Read-only, non-blocking
- No persistence

### Visibility Surfaces
- Location Detail Page
- Global Asset List
- Asset Detail Page

---

## 3. Explicitly Out of Scope (v1)

The following are not permitted without reopening the subsystem:

- Authentication or permissions
- Asset deletion
- Bulk actions
- Background jobs
- Auto-promotion
- Auto-folder discovery
- Audit logs
- Export functionality
- External synchronization
- File-level metadata writes

---

## 4. Sources of Truth

The following documents are authoritative for Assets v1:

- ASSETS_MODEL.md
- ASSET_EDITING_FLOW.md
- LIGHT_ASSET_VALIDATION_DIAGNOSTICS.md
- GLOBAL_ASSET_VIEWS.md
- LOCATION_DETAIL_PAGE_LAYOUT.md

If behavior is not described in one of these documents, it does not exist.

---

## 5. Codex Guardrails

Codex must:

- Reuse shared edit and diagnostics components
- Avoid schema changes
- Avoid implicit behavior
- Prefer TODO markers over assumptions

---

## 6. Completion Criteria

The Assets subsystem is considered complete when:

- No open TODOs reference missing asset behavior
- All asset-related UI paths reuse shared logic
- No asset behavior exists only in chat
- No partial or experimental features remain

---

## Status

Assets Subsystem v1: COMPLETE AND LOCKED
