# Medical Subsystem — Lock & Readiness Specification (v1)

## 1. Purpose

This document formally declares the Medical subsystem complete for v1 and defines what is locked and what is explicitly out of scope.

Any future changes to Medical behavior require reopening the subsystem with a new specification.

---

## 2. Scope Covered (Locked)

The following Medical subsystem components are implemented and locked:

- Canonical Medical Resource records (read-only)
- Medical list view (/medical)
- Medical detail view (/medical/{MedicalFacilityID})
- Read-only sections:
  - Facility Summary
  - Associated Productions
  - Associated Locations
  - Contact Information
  - Notes

No creation, editing, or workflow logic exists in v1.

---

## 3. Explicitly Out of Scope (v1)

The following are not permitted without reopening the subsystem:

- Create, edit, or delete medical resources
- Incident response workflows
- Dispatch, routing, or ETA logic
- Availability or coverage scoring
- Permissions or access control
- Automation or background jobs
- Reporting or exports

---

## 4. Sources of Truth

The following documents are authoritative for the Medical subsystem v1:

- MEDICAL_SUBSYSTEM.md
- PRODUCTION_SUBSYSTEM.md
- LOCATION_DETAIL_PAGE_LAYOUT.md

If behavior is not described in these documents, it does not exist.

---

## 5. Guardrails

- Medical subsystem remains read-only
- No inferred or automatic associations
- No schema changes
- Prefer TODO markers over assumptions

---

## Status

Medical Subsystem v1: COMPLETE AND LOCKED
