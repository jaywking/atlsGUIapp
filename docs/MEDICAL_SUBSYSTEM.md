# Medical Subsystem — Design Specification (v1)

## 1. Purpose

Define Medical resources as first-class, production-aware entities in ATLSApp.

This subsystem provides visibility only in v1 and serves as the foundation for future medical planning and emergency workflows.

---

## 2. Canonical Definition

A Medical Resource represents a verified emergency or urgent care facility relevant to a production and its locations.

Medical resources:
- Are associated with Productions
- May be associated with Locations
- Are not created or edited in v1
- Are informational only

---

## 3. Medical Resource Record (Core Fields)

Required fields:
- MedicalFacilityID (canonical, immutable)
- Facility Name
- Facility Type (ER, Urgent Care, Hospital, Clinic)
- Address (full)
- Phone Number

Optional fields:
- Distance (derived)
- Notes
- Hours (if available)

No routing, availability logic, or scoring in v1.

---

## 4. Relationships

A Medical Resource may be associated with:
- One or more Productions
- One or more Locations

No enforcement or inference beyond explicit associations.

---

## 5. Medical List View

Route:
/medical

yaml
Copy code

Displays:
- Facility Name
- Type
- Associated Production(s)
- Associated Location(s)
- Phone

Actions:
- View Medical Resource

No create/edit/delete actions.

---

## 6. Medical Detail Page

Route:
/medical/{MedicalFacilityID}

yaml
Copy code

Sections (fixed order):

1. Facility Summary
2. Associated Productions
3. Associated Locations
4. Contact Information
5. Notes

All sections are read-only.

---

## 7. Editing Rules (v1)

- Medical resources are read-only
- No UI creation or editing
- No association changes via UI

---

## 8. Constraints (CRITICAL)

- No authentication or permissions
- No emergency workflow logic
- No dispatch logic
- No background jobs
- No schema changes beyond existing Medical tables

---

## 9. Explicit Non-Goals

- Incident response workflows
- Routing or ETA calculation
- Live availability
- Scheduling
- Reporting
- Exports

---

## Status

Medical Subsystem v1: Defined and Read-Only

---

## 2. Implement Read-Only Views

After creating the spec file, implement:

### A. Medical List Page
- Route: /medical
- Read-only list/table
- Derived associations only

### B. Medical Detail Page
- Route: /medical/{MedicalFacilityID}
- Fixed section order
- Navigation back to Productions and Locations

---

## 3. Guardrails

- Do NOT add edit dialogs
- Do NOT add creation flows
- Do NOT infer associations
- Do NOT duplicate Production or Location logic

---

## 4. Completion

When finished:
- Summarize files created/updated
- Confirm no behavior beyond read-only views was added
- Note any assumptions explicitly
