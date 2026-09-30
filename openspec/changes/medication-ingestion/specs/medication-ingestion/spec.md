# Spec Delta

## ADDED Requirements

### Requirement: Natural key for replacing re-uploaded medication data
The system SHALL treat `(actual_date, type, name)` as the natural key identifying "the same" medication-adherence record across uploads, and SHALL upsert on that key — updating `status`, `value`, `unit` and `note` when a re-uploaded row's key matches an existing one — rather than deleting and reinserting by date range.

#### Scenario: Re-uploading the full archive after a status changed
- **WHEN** the user uploads a MyTherapy CSV export where a row's `(actual_date, type, name)` matches a previously stored medication dose, but its `status` or `note` differs from what is stored (e.g. a dose later marked `rejected` with a reason)
- **THEN** celia updates the stored record's `status`, `value`, `unit` and `note` to the newly uploaded values, rather than keeping the old ones or creating a second record

#### Scenario: Re-uploading with no changes
- **WHEN** the user uploads a MyTherapy CSV export identical to one already ingested
- **THEN** no new medication-dose records are created and existing ones are left with the same values (an upsert with identical values, not an error)
