# Asset Editing Flow — Design Specification (v1)

Applies to:
- Photo Assets (PIC###)
- Generic Assets (AST###)
- Folder Assets (FOL###) where applicable

This flow governs editing metadata only. It does not change asset identity or relationships unless explicitly stated.

## 1. Scope & Intent

Purpose:
Define how existing assets may be updated in a controlled, predictable way without undermining referential integrity or introducing implicit behavior.

## 2. Editable vs Immutable Fields

### Immutable Fields (Never Editable)

For all asset types:
- Asset ID
- Asset Type
- External URL
- ProductionID
- LocationsMasterID

### Editable Fields — By Asset Type

Photo Assets (PIC###):
- Asset Name
- Notes
- Hazard Types (multi-select)
- Date Taken
- Visibility Flag (Visible, Hidden only)
- Hero designation is explicitly excluded

Generic Assets (AST###):
- Asset Name
- Notes
- Asset Category (multi-select)
- Hazard Types (if present)
- Visibility Flag (Visible, Hidden)

Folder Assets (FOL###):
- Asset Name
- Notes

Folders do not support:
- Visibility
- Categories
- Hazard Types

## 3. Edit Interaction Model

- Editing is explicit
- No inline edits
- Save / Cancel required
- No auto-save
- No partial saves

## 4. Validation Rules

- Required fields must not be empty
- Enums must be valid
- Visibility = Hero not allowed here
- Block save on validation failure
- No partial updates

## 5. Persistence & Behavior

- Updates written only to Assets table
- Atomic updates
- No cascading changes
- No background reconciliation

## 6. Post-Edit UI Behavior

On success:
- UI updates immediately
- Show confirmation: “Asset updated.”

On failure:
- No UI change
- Show error: “Unable to update asset. Please try again.”

## 7. Explicit Non-Goals

- No bulk editing
- No audit history
- No inferred changes
- No automatic reclassification
