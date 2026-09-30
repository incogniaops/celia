# Design

## Context

glucose-ingestion already built the app skeleton (`app/main.py`, `app/database.py`, `app/config.py`), the container/compose setup, and the upload-route + Jinja2/HTMX pattern (`app/routers/uploads.py`). This change adds a sibling router and parser rather than new infrastructure. A real MyTherapy export is in hand at `data/mytherapy/MyTherapy Archive.csv` (702 rows: 469 `drug`, 196 `activity`, 37 `measurement`; 695 `confirmed` / 7 `rejected`; 11 distinct medications; date range 2026-07-19 to 2026-09-30), plus three monthly PDF reports as a fallback format.

## Goals / Non-Goals

**Goals:**
- Parse the confirmed MyTherapy CSV schema, storing `drug` rows as medication-adherence records.
- Implement the upsert-by-natural-key replace semantics this change's spec delta adds, so re-uploading the full archive after a status changes updates the record instead of duplicating or ignoring it.
- Reuse glucose-ingestion's route/template/container patterns exactly, rather than inventing a second style.

**Non-Goals:**
- Storing the CSV's `activity` and `measurement` rows (steps, weight) — deferred to health-metrics-sync, per the proposal's "What Changes". This change parses them (so a malformed row among them is still caught) but does not persist them.
- The dashboard view of medication adherence (separate capability, `dashboard`).
- A fully-featured PDF table parser — same as glucose-ingestion's PDF fallback, this extracts best-effort summary text only (see Non-Goals in glucose-ingestion's own design.md for the precedent and the `pypdf` choice).

## Decisions

**Upsert, not insert-or-skip**: unlike `GlucoseReading` (immutable sensor readings, `ON CONFLICT DO NOTHING`), `MedicationDose` uses `ON CONFLICT (actual_date, type, name) DO UPDATE` — this change's spec delta requires replace semantics because a medication's logged status can legitimately be corrected in MyTherapy after the fact (e.g. from `confirmed` to `rejected` with a reason added later), and the user re-uploads the same full-history file each time, not an incremental one.
*Alternative considered*: delete all rows in the upload's date range and reinsert. Rejected — MyTherapy's CSV is always a full-history export (not a monthly file like the PDF), so "the overlapping period" is always the entire table; a targeted upsert is simpler and avoids a delete step entirely.

**Only `drug` rows are persisted**: `activity`/`measurement` rows are parsed (to still catch malformed rows across the whole file) but not inserted anywhere, since there is no model for them yet and building one here would pre-empt health-metrics-sync's design decisions for weight/steps (including BR-06's Google-Health-is-authoritative rule, which only makes sense once that source exists).

**Model fields**: `actual_date` (timestamp), `scheduled_date` (nullable timestamp — some rows, e.g. `measurement`/some `activity` rows, have no scheduled time), `type`, `name`, `value` (numeric, nullable), `unit`, `status`, `note` (nullable). Kept close to the CSV's own columns rather than renaming them, since there's no separate business vocabulary for these fields yet.

**File-type detection and PDF fallback**: identical approach to glucose-ingestion — sniff by content (CSV header row vs. `%PDF` magic number), not filename; reuse `pypdf` for the PDF fallback.

## Risks / Trade-offs

- **Silent data loss for `activity`/`measurement` rows**: deferring them (Non-Goals) means uploading today's MyTherapy export does not yet show weight/steps on the dashboard, even though the file contains them. → Mitigation: this is explicitly temporary, tracked as health-metrics-sync's responsibility, not a silent gap — called out in the proposal and here.
- **Upsert masks a legitimate "someone edited history" signal**: because re-uploads overwrite `status`/`note` on key match, there is no audit trail of a changed adherence record. → Accepted for the MVP (single user, no auditability requirement in scope); would need revisiting if multi-user/auditability (Iteration 2, per the product spec) is ever built.
