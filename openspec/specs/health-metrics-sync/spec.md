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

### Requirement: App-managed OAuth authorisation and token refresh
The system SHALL obtain its own Google OAuth refresh token via an authorisation flow it hosts, persist it, and use it to obtain a new access token whenever the stored one has expired, without requiring a human to repeat a manual token exchange for each sync.

#### Scenario: First-time authorisation
- **WHEN** the user visits the Google authorisation link and grants access
- **THEN** celia stores the returned access token, refresh token and expiry, and a subsequent sync can run without further manual steps

#### Scenario: Access token expired at sync time
- **WHEN** a sync is triggered and the stored access token has expired
- **THEN** celia exchanges the stored refresh token for a new access token before calling the Google Health API, and persists the new token and expiry

#### Scenario: Refresh token itself is invalid or revoked
- **WHEN** celia attempts to refresh an access token and Google rejects the refresh token
- **THEN** the sync fails with a message telling the user to re-authorise via the login link, and no partial data is stored

### Requirement: Health metric storage and deduplication
The system SHALL store each synced data point keyed by `(metric_type, recorded_at)`, treating the Google Health API as authoritative for that key — a later sync retrieving the same point SHALL NOT create a duplicate or attempt to reconcile a differing value, mirroring glucose-ingestion's treatment of immutable sensor readings (see glucose-ingestion spec, deduplication requirement).

#### Scenario: Overlapping sync window
- **WHEN** a sync retrieves a data point for a `(metric_type, recorded_at)` already stored from a previous sync
- **THEN** celia does not create a duplicate row and does not change the previously stored value

#### Scenario: Six data types share one storage shape
- **WHEN** celia stores a weight, body-fat, heart-rate, daily-resting-heart-rate, steps or sleep data point
- **THEN** it normalises each into the same `health_metrics` shape (`metric_type`, `recorded_at`, a single numeric `value` with its `unit`, and the full original data point kept for anything the normalised shape doesn't capture, e.g. sleep stage detail)

### Requirement: Store synced timestamps in local time
The system SHALL store each synced data point's `recorded_at` in America/Mexico_City local time, not UTC, for every metric type that carries a time-of-day component.

#### Scenario: A data point is synced from the Google Health API
- **WHEN** celia retrieves a weight, body-fat, heart-rate, steps or sleep data point from the Google Health API (all of which the API reports with a UTC timestamp)
- **THEN** celia converts it to America/Mexico_City before storing it as `recorded_at`, so its calendar day matches the user's own local day

#### Scenario: Daily resting heart rate is a plain date, not a timestamp
- **WHEN** celia retrieves a daily-resting-heart-rate data point, which the Google Health API reports as a date with no time-of-day component
- **THEN** celia stores that date as-is, since there is no time-of-day to convert
