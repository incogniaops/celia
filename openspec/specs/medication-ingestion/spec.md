# Medication Ingestion

## Purpose
Ingest the user's MyTherapy export (CSV preferred, monthly PDF as fallback) so medication-adherence data is visible alongside glucose data without manual data entry.

Source of truth: `docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md`, US-02.

## Requirements

### Requirement: Ingest a MyTherapy CSV export
The system SHALL parse an uploaded MyTherapy CSV export ("Archive.csv" schema: `actual_date, scheduled_date, type, name, value, unit, status, note`) and store each `drug` row as a medication-adherence record.

#### Scenario: Valid MyTherapy CSV uploaded
- **WHEN** the user uploads a MyTherapy CSV export
- **THEN** celia stores each `drug` row as a medication-adherence record (medication name, timestamp, confirmed/rejected status, and the rejection reason from `note` if present)

#### Scenario: CSV also contains activity and measurement rows
- **WHEN** celia ingests a MyTherapy CSV export that also contains `activity` and `measurement` rows (e.g. steps, weight)
- **THEN** it stores those too, subject to the source-precedence rule in health-metrics-sync for any metric also available from Google Health

### Requirement: Ingest a MyTherapy PDF report as fallback
The system SHALL accept a MyTherapy monthly PDF report when the CSV export is not available, extracting what medication-adherence data it can.

#### Scenario: MyTherapy PDF uploaded instead of CSV
- **WHEN** the user uploads a MyTherapy monthly PDF report instead of the CSV
- **THEN** celia extracts what medication-adherence data it can from the PDF, as a fallback

### Requirement: Reject unrecognised files
The system SHALL reject an uploaded file that is not a recognisable MyTherapy CSV or PDF.

#### Scenario: Unrecognised file uploaded
- **WHEN** the user uploads a file that is not a recognisable MyTherapy CSV or PDF
- **THEN** the upload is rejected and the user is told the file could not be recognised

### Requirement: No duplicate records on overlapping re-uploads
The system SHALL replace, not duplicate, previously stored data when a MyTherapy export covering an already-ingested period is uploaded again.

#### Scenario: Overlapping export re-uploaded
- **WHEN** the user uploads a MyTherapy export covering a period already ingested
- **THEN** the newer export replaces the previously stored data for the overlapping period rather than duplicating it

### Requirement: Natural key for replacing re-uploaded medication data
The system SHALL treat `(actual_date, type, name)` as the natural key identifying "the same" medication-adherence record across uploads, and SHALL upsert on that key — updating `status`, `value`, `unit` and `note` when a re-uploaded row's key matches an existing one — rather than deleting and reinserting by date range.

#### Scenario: Re-uploading the full archive after a status changed
- **WHEN** the user uploads a MyTherapy CSV export where a row's `(actual_date, type, name)` matches a previously stored medication dose, but its `status` or `note` differs from what is stored (e.g. a dose later marked `rejected` with a reason)
- **THEN** celia updates the stored record's `status`, `value`, `unit` and `note` to the newly uploaded values, rather than keeping the old ones or creating a second record

#### Scenario: Re-uploading with no changes
- **WHEN** the user uploads a MyTherapy CSV export identical to one already ingested
- **THEN** no new medication-dose records are created and existing ones are left with the same values (an upsert with identical values, not an error)
