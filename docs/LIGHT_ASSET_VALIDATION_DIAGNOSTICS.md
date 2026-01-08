# Light Asset Validation & Diagnostics — Design Specification (v1)

This specification defines non-blocking, read-only diagnostics for assets.

Applies to:
- Photo Assets (PIC###)
- Generic Assets (AST###)
- Folder Assets (FOL###)

---

## 1. Scope & Intent

Purpose:
Surface potential issues or inconsistencies in asset data so a trusted operator can identify and correct them manually.

Diagnostics are:
- Informational only
- Non-blocking
- Never corrective

This system answers:
“Is anything about this asset questionable or incomplete?”

---

## 2. Diagnostic Categories

All diagnostics are advisory only.

### A. Missing or Weak Context

- PIC### linked to ProductionID but missing LocationsMasterID → INFO
- PIC### missing ProdLocID (when ProductionID is present) → INFO
- FOL### missing ProdLocID → INFO
- AST### linked only to ProductionID (no location) → OK (do not flag)

---

### B. Metadata Gaps

- PIC### missing Asset Name → CHECK
- PIC### missing Notes → INFO
- PIC### with empty Hazard Types → INFO
- AST### with empty Asset Category → CHECK

---

### C. Visibility Inconsistencies

- Asset marked Hidden but surfaced in Location Detail sections → CHECK
- More than one Hero photo for the same LocationsMasterID → WARNING
  (defensive check; should not normally occur)

---

### D. External URL Issues

- Missing External URL → WARNING
- Invalid External URL format → WARNING

No reachability checks are required in v1.

---

## 3. Severity Levels

Use only the following severity labels:

- INFO  
  Optional improvement, no action required.

- CHECK  
  Likely oversight; user should review.

- WARNING  
  Invalid or contradictory state; should be addressed.

Do NOT introduce ERROR severity.

---

## 4. Presentation Rules

- Diagnostics must be:
  - Read-only
  - Non-blocking
  - Visually subtle

Allowed presentation:
- Small badges
- Inline labels
- Tooltips or expandable text (optional)

Not allowed:
- Modals
- Toasts
- Alerts
- Blocking banners

---

## 5. Placement

### Asset-Level (Primary)

- Diagnostics appear inline with each asset wherever assets are rendered:
  - Location Detail page
  - Promoted Photo Assets
  - Other Assets sections

Each asset may show zero or more diagnostics.

---

### Page-Level Summary (Optional)

- If multiple assets on a page have diagnostics:
  - Show a small summary line (e.g., “3 assets have checks”)
- Summary must be non-interruptive.

---

## 6. Computation Rules

- Diagnostics may be computed:
  - At read time in the API, OR
  - In the UI using returned asset data
- Diagnostics must NOT be stored.
- No new database fields may be added.

---

## 7. Constraints (CRITICAL)

- Do NOT enforce rules
- Do NOT auto-fix data
- Do NOT block:
  - Asset editing
  - Photo promotion
  - Folder registration
- Do NOT introduce authentication or permissions
- Do NOT add background jobs

This system provides visibility only.

---

## 8. Explicit Non-Goals

- No remediation suggestions
- No scoring or ranking
- No bulk actions
- No audit logging

Diagnostics exist solely to inform.

---

After creating the file, proceed with implementation.
Summarize diagnostics implemented and where computation occurs (API vs UI).
