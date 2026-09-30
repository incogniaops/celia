# Glucose Ingestion

## Purpose
Ingest the user's FreeStyle Libre glucose export from LibreView (CSV and/or PDF), the sole glucose source in celia, so glucose history is available to the dashboard without manual data entry.

Source of truth: `docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md`, US-01.

## Requirements

### Requirement: Ingest a LibreView CSV export
The system SHALL parse an uploaded LibreView CSV export and store each historic reading, manual scan, insulin entry and carbohydrate entry with its original timestamp.

#### Scenario: Valid LibreView CSV uploaded
- **WHEN** the user uploads a LibreView CSV export file
- **THEN** celia parses the Device Timestamp and Record Type columns and stores each historic reading, manual scan, insulin entry and carbohydrate entry with its original timestamp

#### Scenario: CSV "Número de serie" column is not the physical sensor serial
- **WHEN** celia parses the "Número de serie" column of a LibreView CSV export
- **THEN** it treats the value as a device/app-installation identifier (a UUID), not the physical sensor's serial number (an alphanumeric code such as `3MH01ME1GZD`), and does not use it for sensor attribution or the sensor log

### Requirement: Ingest a LibreView PDF report
The system SHALL accept a LibreView PDF report as an alternative to the CSV, extracting the glucose summary data it contains.

#### Scenario: LibreView PDF uploaded instead of CSV
- **WHEN** the user uploads a LibreView PDF report instead of a CSV
- **THEN** celia extracts the glucose summary data it contains and stores it, noting that PDF ingestion may be less granular than CSV

### Requirement: Reject unrecognised files
The system SHALL reject an uploaded file that does not match the expected LibreView format.

#### Scenario: Unrecognised file uploaded
- **WHEN** the user uploads a file that does not match the expected LibreView CSV or PDF format
- **THEN** the upload is rejected and the user is told the file could not be recognised

### Requirement: No duplicate readings on overlapping re-uploads
The system SHALL NOT create duplicate glucose readings when an uploaded export overlaps a period already ingested.

#### Scenario: Overlapping export re-uploaded
- **WHEN** the user uploads a Libre export that overlaps a period already ingested
- **THEN** celia does not create duplicate readings for the overlapping period
