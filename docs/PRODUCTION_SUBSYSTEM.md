# Production Subsystem — Design Specification (v1)

## 1. Purpose

Define Productions as first-class entities in ATLSApp and establish them as the top-level organizational context for locations, assets, and future subsystems.

This subsystem is read-only in v1.

---

## 2. Canonical Definition

A Production represents a single show, event, or project supported by ATLS.

A Production:
- Exists independently of locations
- May span multiple locations
- May have multiple associated assets
- Serves as the primary organizational boundary

---

## 3. Production Record (Core Fields)

Required fields:
- ProductionID (canonical, immutable)
- Production Name
- Production Code / Abbreviation (e.g., AMCL, RIP)
- Status (Active, Inactive, Archived)

Optional fields:
- Notes

No schedules, dates, contacts, or billing fields in v1.

---

## 4. Relationships

A Production may be associated with:
- Locations (via ProdLoc records)
- Assets (PIC###, AST###, FOL###)

No bidirectional enforcement beyond references.

---

## 5. Production List View

Route:
/productions

yaml
Copy code

Displays:
- Production Name
- Code
- Status
- Count of Locations
- Count of Assets

Actions:
- View Production

No create, edit, delete actions.

---

## 6. Production Detail Page

Route:
/productions/{ProductionID}

yaml
Copy code

Sections (fixed order):

1. Production Summary
2. Locations
3. Assets
4. Notes

### 6.1 Production Summary
- Name
- Code
- Status

### 6.2 Locations
- List of associated Locations
- Links to Location Detail pages

### 6.3 Assets
- List of assets associated with this Production
- Reuse Global Asset List component with Production filter applied

### 6.4 Notes
- Read-only notes

---

## 7. Editing Rules (v1)

- Production records are read-only
- No UI-based create/edit/delete
- No status changes via UI

---

## 8. Constraints (CRITICAL)

- No authentication or permissions
- No scheduling logic
- No medical logic
- No automation
- No background jobs
- No schema changes outside Production tables

---

## 9. Explicit Non-Goals

- Call sheets
- Schedules
- Medical planning
- Staffing
- Billing
- Reporting
- Exports

---

## Status

Production Subsystem v1: Defined and Read-Only

---

## 2. Implement Read-Only Views

After creating the spec file, implement:

### A. Production List Page
- Route: /productions
- Read-only table/list
- Counts derived from existing relationships

### B. Production Detail Page
- Route: /productions/{ProductionID}
- Fixed section order per spec
- Reuse existing components where possible
- No editing logic

---

## 3. Guardrails

- Do NOT add edit dialogs
- Do NOT add creation flows
- Do NOT infer relationships
- Do NOT duplicate asset logic
- Prefer reuse over new components

---

## 4. Completion

When finished:
- Summarize files created/updated
- Confirm no behavior beyond read-only views was added
- Note any assumptions explicitly
