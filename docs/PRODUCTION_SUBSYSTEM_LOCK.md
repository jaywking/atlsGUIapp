# Production Subsystem — Lock & Readiness Specification (v1)

## 1. Purpose

This document declares the Production subsystem complete for v1 and defines what is locked and what is out of scope.

Any future changes require reopening the subsystem with a new spec.

---

## 2. Scope Covered (Locked)

- Canonical Production record (read-only)
- Production list view (/productions)
- Production detail view (/productions/{ProductionID})
- Read-only sections:
  - Summary
  - Locations
  - Assets (via shared asset list)
  - Notes
- Derived counts for locations and assets

---

## 3. Explicitly Out of Scope (v1)

- Create/edit/delete productions
- Status transitions
- Scheduling
- Medical planning
- Permissions
- Automation
- Background jobs
- Reporting/export

---

## 4. Sources of Truth

Authoritative documents:
- PRODUCTION_SUBSYSTEM.md
- GLOBAL_ASSET_VIEWS.md
- ASSETS_MODEL.md

If behavior is not described in these, it does not exist.

---

## 5. Guardrails

- Read-only only
- No inferred relationships
- No schema changes
- Prefer TODOs over assumptions

---

## Status

Production Subsystem v1: COMPLETE AND LOCKED
