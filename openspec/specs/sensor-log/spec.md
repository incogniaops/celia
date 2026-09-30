# Sensor Log

## Purpose
Let the user manually record which FreeStyle Libre sensor (serial, start/end dates, start/end status codes) he wore during a given period, so glucose history stays correctly attributed to a physical sensor even though sensors don't all last the same number of days — and so sensors that failed early can be spotted. This is the sole manual-data-entry exception in celia (see A-06, A-07).

Source of truth: `docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md`, US-06.

## Requirements

### Requirement: Record a sensor period
The system SHALL allow the user to manually add a sensor-log entry with serial, start date and start status code, initially open-ended, and later close it with an end date and end status code.

#### Scenario: New sensor started
- **WHEN** the user adds a log entry with a sensor's serial, start date, and the status code shown in the FreeStyle LibreLink app's "Acerca de" screen at that time
- **THEN** celia stores it as an open-ended period (no end date yet)

#### Scenario: Sensor period closed
- **WHEN** the user records a sensor's end date and its status code at that point, whether it lasted the typical 14–15 days or failed earlier
- **THEN** the entry is closed for that period, with both its start and end status codes stored

#### Scenario: Status code unavailable at close time
- **WHEN** the user closes a sensor-log entry after it has aged out of the app's "last 3 sensors" list
- **THEN** celia still allows the end date to be recorded, with the end status code left blank rather than blocking the update

### Requirement: No overlapping sensor periods
The system SHALL reject a sensor-log entry whose date range would overlap an existing entry.

#### Scenario: Overlapping entry attempted
- **WHEN** a new sensor-log entry's date range would overlap an existing entry
- **THEN** celia rejects it and tells the user which existing entry conflicts

### Requirement: Surface sensor attribution on the dashboard
The system SHALL show the active sensor (and its status code(s)) for any given date on the dashboard, and SHALL mark periods with no matching sensor-log entry as unlogged without blocking the rest of the view.

#### Scenario: Dashboard shows sensor for a date
- **WHEN** the user views the dashboard and one or more sensor-log entries exist
- **THEN** the active sensor for any given date is shown alongside the glucose trend for that date, together with its status code(s)

#### Scenario: Glucose period has no matching sensor-log entry
- **WHEN** a period of the glucose timeline has no matching sensor-log entry
- **THEN** that period is marked as having an unlogged sensor, without blocking the rest of the view

### Requirement: Status codes are opaque
The system SHALL store the "Estado" status code as an opaque reference string and SHALL NOT interpret or decode it, since its meaning is undocumented by Abbott.

#### Scenario: Status code stored without interpretation
- **WHEN** celia stores a sensor-log entry's start or end status code
- **THEN** it keeps the value as an opaque string for the user's own reference, without attempting to decode or attach meaning to it
