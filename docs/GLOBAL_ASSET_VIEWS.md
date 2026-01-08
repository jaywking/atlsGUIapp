# Global Asset List & Asset Detail Pages — Design Specification (v1)

This specification defines system-wide asset visibility and inspection surfaces.
It does **not** introduce new behavior, only new views.

---

## 1. Scope & Intent

### Purpose

Provide a **central, system-wide view** of all assets and a **single-asset inspection page**, without changing asset behavior, permissions, or lifecycle rules.

This answers:

* “What assets exist in the system?”
* “Where is this asset used?”
* “What metadata does this asset have?”

---

## 2. Asset List Page (Global)

### Route

```
/assets
```

---

### Assets Included

The list includes **all assets** in the Assets table:

* PIC###
* AST###
* FOL###

No filtering by default.

---

### Default Columns (Required)

Each asset row must display:

* Asset ID
* Asset Name
* Asset Type
* Asset Category (if applicable)
* Production(s)
* Locations Master
* Visibility Flag
* Diagnostic badge summary (if any)

---

### Sorting (Default)

* Primary: Asset Type
* Secondary: Asset Name (A–Z)

---

### Filtering (v1)

Filtering is **client-side** and optional.

Supported filters:

* Asset Type
* Production
* Locations Master
* Visibility Flag
* Has Diagnostics (yes/no)

No advanced query language.

---

### Row Actions

Each row provides explicit actions:

* View Asset
* Edit Asset

No destructive actions.

---

## 3. Asset Detail Page

### Route

```
/assets/{AssetID}
```

---

### Purpose

Provide a **single authoritative view** of an asset’s metadata, diagnostics, and relationships.

---

### Sections (Fixed Order)

1. Asset Summary
2. Diagnostics (if any)
3. Metadata
4. Associations
5. References
6. Actions

---

### 3.1 Asset Summary

Displays:

* Asset ID
* Asset Name
* Asset Type
* Visibility Flag
* Hero status (PIC### only, read-only)

---

### 3.2 Diagnostics

* Inline diagnostics exactly as defined in:
  `LIGHT_ASSET_VALIDATION_DIAGNOSTICS.md`
* Same severity and presentation rules
* Read-only

---

### 3.3 Metadata

Editable fields only:

* Uses **Asset Editing UI**
* Same validation rules
* No duplication of edit logic

---

### 3.4 Associations

Displays:

* Production(s)
* Locations Master
* ProdLocID (if present)

No editing here.

---

### 3.5 References

Displays where the asset is surfaced:

* Location Detail pages
* Hero usage (PIC###)
* Folder membership (informational only)

No inference.

---

### 3.6 Actions

Explicit actions only:

* Edit Asset
* Navigate to related Location(s)
* Navigate to Production(s)

No delete, no promote, no hero changes.

---

## 4. Diagnostics Integration

* Same diagnostics logic as Location Detail
* No recomputation rules added
* No persistence

---

## 5. Constraints (CRITICAL)

* No schema changes
* No auth or permissions
* No destructive actions
* No bulk actions
* No automation
* No background jobs

This is a **visibility layer only**.

---

## 6. Explicit Non-Goals

* No asset creation
* No asset deletion
* No bulk editing
* No audit history
* No export functionality

---

## 7. Relationship to Existing UI

* Location Detail remains the **primary contextual view**
* Asset List / Detail provide **system-level inspection**
* Editing behavior is shared, not duplicated

---

## Status

This specification is **authoritative** for v1.

---

## What Happens Next

### Step 1 (required)

Tell Codex to:

* Create
  `docs/GLOBAL_ASSET_VIEWS.md`
* Paste this spec verbatim

### Step 2

Codex implements:

* `/assets` list
* `/assets/{AssetID}` detail page
* Shared edit and diagnostics components
