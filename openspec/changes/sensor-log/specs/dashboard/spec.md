# Spec Delta

## ADDED Requirements

### Requirement: Sensor log overlap view
The system SHALL show a "Sensor log" section listing every sensor-log entry that overlaps the currently-selected date range, and SHALL show how many days within that range have no matching entry, without blocking the rest of the dashboard.

#### Scenario: Entries overlap the selected range
- **WHEN** the user views the dashboard for a date range and one or more sensor-log entries overlap it
- **THEN** the "Sensor log" section lists each overlapping entry (serial, start date, start status code, end date and end status code if closed)

#### Scenario: Part of the range has no matching entry
- **WHEN** a portion of the selected range has no overlapping sensor-log entry
- **THEN** the section shows how many days in the range are unlogged, without blocking any other part of the dashboard

#### Scenario: No sensor-log entries at all
- **WHEN** no sensor-log entries exist yet
- **THEN** the section shows that the whole selected range is unlogged, consistent with the dashboard's existing empty-state handling for other sources
