# Assets Model – Canonical Design

Version: v1.0 (Design Locked)
Date: 2026-01-05 21:46 -0500

## 1. Purpose

This document defines the **canonical Assets model** for ATLSApp. It captures the complete design intent, rules, and boundaries for managing references to folders, documents, and photos (including hero photos) associated with Productions and Locations.

This model is intentionally **reference-only**. ATLSApp does not store files, upload binaries, or manage permissions. All assets are external (primarily Google Drive) and are linked into the system via stable URLs.

This document is the authoritative source for all future Assets-related development. Other project documents should reference this file rather than duplicating its contents.

---

## 2. Core Principles

- Assets are **references**, not stored content.
- Files remain in their original production folders.
- Production context is preserved at all times.
- Locations may aggregate assets from multiple productions.
- Promotion of individual files to Assets is **explicit and manual**.
- The system never crawls or scans Google Drive.

---

## 3. Asset Classes & ID Prefixes

Assets use **human-facing identifiers** with semantic prefixes. These are not system primary keys; Notion Page IDs remain authoritative.

| Asset Class | Prefix | Example | Notes |
|------------|--------|---------|-------|
| Photo / Image | PIC | PIC012 | Used for promoted photos only |
| Folder | FOL | FOL004 | Used for referenced folders |
| Generic Asset | AST | AST021 | Documents, PDFs, spreadsheets, etc. |

Rules:
- Separate numeric sequences per prefix
- Prefix is determined by intent, not file extension
- Prefix expansion is allowed only when an asset class has distinct behavior or metadata

---

## 4. Physical File Organization (Assumed)

ATLSApp does not enforce file structure but assumes the following **canonical production pattern**:

```
Production Root
└── Locations
    └── LocationName (or LOC### – Name)
        └── Photos
            ├── image files
```

Photos always live inside the production context where they were captured.

---

## 5. Assets Database – Schema Overview

All asset types live in a **single Assets table**.

### 5.1 Core Identity Fields (All Assets)

- Asset ID (Title) – PIC###, FOL###, or AST###
- Asset Name (Text)
- Asset Type (Select): File or Folder
- Asset Category (Multi-select)
- External URL (URL): Google Drive file or folder link

### 5.2 Context & Relations

- ProductionID (Relation) – Required
- ProdLocID (Relation) – Required when asset is production-location specific
- LocationsMasterID (Relation) – Required when asset relates to a real-world location
- Source Production (Relation) – Optional, for reused assets

Rules:
- Folder assets always require ProductionID
- Photo assets always require ProductionID, ProdLocID, and LocationsMasterID

#### Generic Assets (AST###) - Location Context Rules

- Generic Assets (AST###) must always be linked to a ProductionID.
- Generic Assets (AST###) MAY be linked to:
  - ProdLocID (production-specific location)
  - LocationsMasterID (canonical location)
- Generic Assets (AST###) are NOT required to have location relations unless the asset content is location-specific.

Examples:
- Scripts, schedules, call sheets -> ProductionID only
- Location hazard assessment PDF -> ProductionID + ProdLocID + LocationsMasterID
- Permit covering a specific site -> ProductionID + LocationsMasterID

---

## 6. Asset Categories (Default Seed Values)

Asset Category is a **flexible multi-select**. The initial default values are:

- Call Sheet
- Incident
- Location
- Schedule
- Script
- Other

Categories are descriptive, not exclusive. Additional categories may be added without schema changes.

### Asset Category Governance

- Asset Categories are shared, environment-wide values.
- Categories may be added or modified only by administrators.
- Categories should represent stable usage groupings, not one-off labels.
- Categories must not encode file type or asset class.
- New categories should be documented when introduced.

---

## 7. Photo Assets (PIC###)

Photo assets represent **explicitly promoted individual images**. Not all photos are assets; only those that require independent reference.

### 7.1 Required Context

Every Photo Asset must be linked to:

- ProductionID
- ProdLocID
- LocationsMasterID

This ensures both production-specific and canonical location context.

### 7.2 Photo-Specific Metadata

- Notes (Text, optional)
- Hazard Types (Multi-select, optional)
- Date Taken (Date, optional)
- Visibility Flag (Select, optional)
  - Hero
  - Visible
  - Internal

---

## 8. Hero Photo Rules

A Hero Photo is not a separate entity. It is:

- A Photo Asset (PIC###)
- With Visibility Flag = Hero

Rules:
- Only one Hero photo per LocationsMasterID
- Selection is explicit and manual
- The system never auto-selects or replaces Hero photos

The Hero photo is displayed prominently on the Location detail page and links back to the original Drive file.

### Hero Photo Enforcement & Conflict Resolution

- Only one Photo Asset (PIC###) may have Visibility Flag = Hero per LocationsMasterID.
- If a user attempts to assign a second Hero photo for the same LocationsMasterID:
  - The system must block the action OR
  - Require explicit confirmation to replace the existing Hero.
- The previously designated Hero must be automatically downgraded (e.g., to Visible).
- Silent overrides are not permitted.
- At no time may two Hero photos exist simultaneously for the same LocationsMasterID.

Enforcement may occur in:
- UI
- Service layer
- Automation logic

---

## 9. Folder Assets (FOL###)

Folder assets represent meaningful containers, such as:

- Production root folder
- Locations folder
- Location-specific Photos folder

Folder assets:
- Are never scanned or enumerated by the system
- Exist solely to provide navigation and context

---

## 10. What the System Explicitly Does NOT Do

- No file uploads
- No binary storage
- No Google Drive crawling or scanning
- No thumbnail generation
- No permission management
- No automatic asset creation

All file access is handled directly by Google Drive via user authentication.

---

## 11. Future Expansion Guardrails

The Assets model is expected to evolve. Expansion is allowed only when:

- A new asset class has distinct behavior or metadata
- The class is routinely referenced independently

Examples of potential future prefixes:
- MAP### (annotated maps)
- VID### (video or drone footage)

File extensions alone do not justify new prefixes.

---

## 12. Canonical Status

This document is the **single source of truth** for Assets behavior in ATLSApp.

All future implementation, UI, and automation decisions related to Assets must align with this model unless this document is explicitly revised.
