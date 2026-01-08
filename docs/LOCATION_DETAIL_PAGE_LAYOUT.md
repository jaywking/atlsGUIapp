# Location Detail Page Layout Specification (Approved)

This document captures the approved Location Detail Page layout and binding rules as provided in ChatGPT.
It is authoritative for implementation until a newer version is approved.

---

## 1. Page Purpose

Render a read-only, canonical Location Detail Page that:
- Preserves production context
- Surfaces only explicitly promoted assets
- Avoids Drive crawling or inference
- Is safe for iterative refinement

---

## 2. Section Order (MANDATORY)

Render sections in this exact order:

1. Header / Identity
2. Hero Photo
3. Core Location Information
4. Photo Folders (by Production) - with thumbnails
5. Promoted Photo Assets
6. Other Assets (Non-Photo)
7. Related Productions

Do not reorder or merge sections.

---

## 3. Section Requirements

### 3.1 Header / Identity

Render:
- Location Name (primary)
- LocationsMasterID (secondary)

No actions.
No images.
No production context.

### 3.2 Hero Photo

Data source:
- Photo Asset (PIC###)
- Visibility Flag = Hero
- Linked to LocationsMasterID

Rules:
- Render exactly one hero photo if present
- If none exists, show placeholder text: "No hero photo selected"
- Clicking image opens External URL (Google Drive) in new tab
- No carousel, no gallery, no inference

### 3.3 Core Location Information

Render existing Locations Master fields only.
- Read-only
- Hide empty fields
- No asset links
- No production data

### 3.4 Photo Folders (by Production)

Data source:
- Folder Assets (FOL###)
- Asset Category includes "Locations"
- Linked to:
  - LocationsMasterID
  - ProductionID

For each folder:
- Show Production Name
- Show "View Photos" link -> External URL (Drive folder)

#### Thumbnails (IMPORTANT)

- Thumbnails may be shown ONLY if:
  - Photo Assets (PIC###) exist
  - Linked to same LocationsMasterID AND ProductionID
- Max 1-3 thumbnails per production
- Thumbnails come ONLY from promoted Photo Assets
- Do NOT scan Drive folders
- If no promoted photos exist, show no thumbnails

Empty state:
- If no folder assets exist, show helper text:
  "No photo folders linked for this location."

### 3.5 Promoted Photo Assets

Inclusion:
- Photo Assets (PIC###)
- Visibility Flag = Visible
- Linked to LocationsMasterID
- Exclude Hero photo

Render each as:
- Thumbnail
- Asset Name
- Notes (if present)
- Source Production
- Date Taken (if present)

Behavior:
- Clicking opens External URL (Drive file)
- No gallery or lightbox
- No auto-promotion

Ordering:
1. Photos with Hazard Types populated
2. Then alphabetical by Asset Name

Hide section entirely if empty.

### 3.6 Other Assets (Non-Photo)

Inclusion:
- Generic Assets (AST###)
- Linked to LocationsMasterID

Render as list or table:
- Asset Name
- Asset Category
- Source Production
- Action link -> External URL

No previews.
No thumbnails.
No editing.

Hide section if empty.

### 3.7 Related Productions

Render list of Productions associated with this LocationsMasterID via:
- ProdLocID relations
- OR Assets linked to this location

Informational only.
No actions required.

---

## 4. Constraints (CRITICAL)

- Do NOT scan Google Drive
- Do NOT enumerate folder contents
- Do NOT infer "best" or "latest" photos
- Do NOT auto-select Hero photos
- Do NOT modify assets
- Do NOT introduce new fields or schema changes

Only render what is explicitly present in the database.

---

## 5. Hero Photo Enforcement (Support Only)

UI must support:
- Displaying current Hero
- Replacing Hero only via explicit action (future admin UI)

Do NOT silently override Hero photos.

---

## 6. Output Requirements

- Implement the page layout and data binding
- Leave TODO markers where admin actions will later be added
- Keep styling minimal and consistent with existing app
- Prefer clarity over density

---

## 7. Deliverables

- Updated Location Detail Page implementation
- Brief summary of:
  - Which sections were implemented
  - Any assumptions made (must be minimal)
  - Any TODOs left intentionally

Do not proceed beyond this page.
