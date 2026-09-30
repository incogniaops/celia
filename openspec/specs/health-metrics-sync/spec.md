# Health Metrics Sync

## Purpose
Sync weight, body fat, heart rate, resting heart rate, steps and sleep from the Google Health API (fed by the user's Wyze scale and Xiaomi smartband via Health Connect), so they are visible alongside glucose data without a manual export step.

Source of truth: `docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md`, US-03, A-03, A-08.

## Requirements

### Requirement: Sync weight, body fat, heart rate and resting heart rate
The system SHALL retrieve weight, body-fat, heart-rate and daily-resting-heart-rate data points from the Google Health API (`GET https://health.googleapis.com/v4/users/me/dataTypes/{dataType}/dataPoints`, scope `googlehealth.health_metrics_and_measurements.readonly`) and store them.

#### Scenario: Sync triggered with complete setup
- **WHEN** a sync is triggered and the account is linked at `fitbit.google.com/auth/signup` and Health Connect is connected inside the Google Health app (Connections → Partner apps)
- **THEN** celia retrieves new weight, body-fat, heart-rate and daily-resting-heart-rate records since the last successful sync (or, on first sync, as far back as each type's API response returns) and stores them

### Requirement: Sync steps and sleep
The system SHALL retrieve steps (scope `activity_and_fitness.readonly`) and sleep (scope `sleep.readonly`) data points, paginating via `nextPageToken` to retrieve more than the most recent page.

#### Scenario: Steps and sleep sync requires pagination
- **WHEN** celia syncs steps or sleep data
- **THEN** it follows `nextPageToken` across pages rather than relying on a single unpaginated call, since these types return only a small recent window per page by default

### Requirement: Surface sync status and failures
The system SHALL show when a sync last ran and whether it succeeded, and SHALL leave existing data unchanged on failure.

#### Scenario: Sync completes
- **WHEN** a sync completes
- **THEN** the user sees when it last ran and whether it succeeded

#### Scenario: Sync fails or account is not linked
- **WHEN** the Google Health API is unreachable, returns an error, or the account/Health Connect connection is incomplete (`ACCOUNT_NOT_LINKED` or similar)
- **THEN** celia shows the sync failed with the reason, and existing data is left unchanged

### Requirement: No duplicate records across syncs
The system SHALL NOT create duplicate data points when a sync retrieves records already stored from a previous sync.

#### Scenario: Overlapping sync
- **WHEN** a new sync retrieves records that overlap previously synced data
- **THEN** celia does not create duplicate readings

### Requirement: Respect per-data-type historical limits
The system SHALL treat the absence of data before a data type's available range as expected, not as an error, and SHALL NOT assume one data type's coverage implies another's.

#### Scenario: Dashboard viewed for a date before a type's coverage
- **WHEN** the user views the dashboard for a date earlier than a given data type's available range (e.g. before 2026-08-19 for weight, for this user)
- **THEN** the absence of data there is not shown as an error for that type, and does not affect other data types that may cover that date

### Requirement: Google Health is authoritative over MyTherapy for overlapping metrics
The system SHALL treat Google Health API data as authoritative over MyTherapy-sourced data for weight and step-count metrics on dates where both are present.

#### Scenario: Same date has weight/steps from both sources
- **WHEN** both the MyTherapy export and the Google Health API provide a value for weight or step count on the same date
- **THEN** the Google Health value is shown as the primary figure on the dashboard, and the MyTherapy value for that date/metric is kept for reference only
