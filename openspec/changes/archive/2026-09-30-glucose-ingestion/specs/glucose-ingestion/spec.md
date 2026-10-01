# Spec Delta

## ADDED Requirements

### Requirement: Deduplication key for overlapping re-uploads
The system SHALL treat a glucose reading as a duplicate of a previously stored reading only when its source device timestamp and record type match an existing reading exactly, rather than replacing an entire file's worth of data on re-upload. This is necessary because LibreView CSV exports are cumulative (a single export can contain a device's full history, not just data since the last export).

#### Scenario: Re-uploading a superset export
- **WHEN** the user uploads a LibreView CSV export whose rows are a superset of a previously ingested export (same device timestamps and record types, plus some new ones)
- **THEN** celia stores only the rows whose (timestamp, record type) pair was not already stored, and leaves previously stored readings unchanged

#### Scenario: Two exports disagree on a value for the same timestamp and type
- **WHEN** two uploaded exports both contain a reading for the same device timestamp and record type, but with different glucose values
- **THEN** celia keeps the first value stored and does not overwrite it with the later upload's value, since (timestamp, record type) is treated as a stable identity, not a value to reconcile
