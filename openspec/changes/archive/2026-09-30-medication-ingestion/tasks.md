# Tasks

## 1. Database model and migration

- [x] 1.1 Define the `MedicationDose` SQLAlchemy model (`actual_date`, nullable `scheduled_date`, `type`, `name`, nullable `value`, `unit`, `status`, nullable `note`, unique constraint on `(actual_date, type, name)`) and verify a unit test asserts the constraint is present on the table
- [x] 1.2 Write the second Alembic migration creating the `medication_doses` table, and verify `alembic upgrade head` succeeds against the running Postgres instance
- [x] 1.3 Add an upsert helper using `INSERT ... ON CONFLICT (actual_date, type, name) DO UPDATE` (updating `status`, `value`, `unit`, `note`) and verify a unit test confirms re-inserting the same key with a changed `status` updates the existing row rather than creating a second one

## 2. MyTherapy CSV/PDF parser

- [x] 2.1 Implement CSV parsing for the confirmed MyTherapy schema (`actual_date, scheduled_date, type, name, value, unit, status, note`), returning only `drug` rows as medication-dose records, and verify a unit test against a trimmed fixture derived from `data/mytherapy/MyTherapy Archive.csv` parses the expected row count and values (medication name, status, note)
- [x] 2.2 Parse `activity` and `measurement` rows too (to still catch malformed rows across the whole file) but discard them rather than storing them, per this change's Non-Goals, and verify a unit test confirms they are recognised and counted but not present in the returned medication-dose records
- [x] 2.3 Implement file-type sniffing (MyTherapy CSV header vs. `%PDF` magic number vs. unrecognised) and verify a unit test covers all three cases
- [x] 2.4 Implement the PDF fallback extraction using `pypdf` and verify a unit test against a trimmed sample PDF (derived from `data/mytherapy/MyTherapy_2026_09.pdf`) extracts summary text without raising
- [x] 2.5 Skip individually malformed rows within an otherwise-valid CSV, collecting a count and reason, and verify a unit test with an injected bad row confirms the good rows still ingest and the bad-row count is reported

## 3. Upload route and form

- [x] 3.1 Add `POST /uploads/mytherapy` accepting a multipart file upload, wiring the parser and upsert helper together, and verify an integration test uploads the trimmed fixture and confirms the expected medication doses are queryable afterwards
- [x] 3.2 Add the Jinja2/HTMX upload form template (matching the `/uploads/libre` pattern) and verify `GET /uploads/mytherapy` renders a working file-upload form
- [x] 3.3 Implement rejection responses for unrecognised files, and confirm re-uploading an export with a changed `status` for an existing `(actual_date, type, name)` updates that row rather than duplicating it, verified by two integration tests

## 4. End-to-end verification

- [x] 4.1 Run the full flow against the real sample export (`data/mytherapy/MyTherapy Archive.csv`) in the local Podman container, and verify the expected number of `drug` rows are stored (466 unique after deduplicating 3 same-key rows, out of 469 `drug` rows in the current real export) and that re-uploading the same file changes nothing
