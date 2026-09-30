# Proposal

## Why

Medication adherence is the second of celia's three MVP data sources and the second real dataset already in hand (`data/mytherapy/`: a full-history CSV export plus three monthly PDF reports). glucose-ingestion already established the app skeleton, upload-form pattern and containerised dev loop this change reuses directly, so implementing medication-ingestion next keeps momentum on real, testable data rather than building ahead into health-metrics-sync (whose Google Health integration has no code yet).

## What Changes

- Add a FastAPI upload endpoint and upload form for a MyTherapy export (CSV preferred, monthly PDF as fallback), following the same route/template pattern as `/uploads/libre`.
- Add a parser for the confirmed MyTherapy CSV schema (`actual_date, scheduled_date, type, name, value, unit, status, note`), storing `drug` rows as medication-adherence records (medication name, timestamp, confirmed/rejected status, rejection reason from `note`).
- Add a Postgres table for medication doses, upserting on a natural key so a re-uploaded export **replaces** a changed row instead of creating a duplicate (per the existing spec's requirement 4) or silently keeping a stale one (unlike glucose-ingestion's immutable-reading "keep first" rule — see the spec delta below for why this capability needs the opposite rule).
- Reject files that match neither the MyTherapy CSV header nor a PDF.
- **Deferred, not built in this change**: the CSV's `activity` and `measurement` rows (steps, weight) — the existing medication-ingestion spec says celia stores these too, "subject to the source-precedence rule in health-metrics-sync." That capability doesn't exist as code yet, and building its weight/steps model as a side effect of this change would implement two capabilities out of order. This change parses and discards those rows for now; a future health-metrics-sync change will pick them up alongside the Google Health API sync it is already scoped to build.

## Capabilities

### New Capabilities
(none — this change implements an existing capability)

### Modified Capabilities
- `medication-ingestion`: add a requirement defining the natural key for "replace, not duplicate" (requirement 4): `(actual_date, type, name)`. The existing spec says a re-upload covering an already-ingested period must replace prior data, but doesn't say what identifies "the same" record — without this, a reasonable-looking implementation could delete-and-reinsert by date range, which is unnecessary here (the CSV is always a full-history export, not a monthly file, so every upload covers the same period: all of it).

## Impact

- **New code**: a `medication` parser module, a `MedicationDose` model + migration, and a `medication` upload route + templates, all following the structure glucose-ingestion already established (`app/parsers/`, `app/models.py`, `app/routers/`).
- **New dependency**: none beyond what glucose-ingestion already added (`pypdf` is already in `pyproject.toml` for the PDF fallback).
- **Database**: a second Alembic migration, creating the `medication_doses` table.
- **No impact** on glucose-ingestion. No impact on health-metrics-sync's future model, since this change explicitly does not store `activity`/`measurement` rows.
