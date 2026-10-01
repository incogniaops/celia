# Spec Delta

## ADDED Requirements

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
