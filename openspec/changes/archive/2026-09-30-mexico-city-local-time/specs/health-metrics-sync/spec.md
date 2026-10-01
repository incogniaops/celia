# Spec Delta

## ADDED Requirements

### Requirement: Store synced timestamps in local time
The system SHALL store each synced data point's `recorded_at` in America/Mexico_City local time, not UTC, for every metric type that carries a time-of-day component.

#### Scenario: A data point is synced from the Google Health API
- **WHEN** celia retrieves a weight, body-fat, heart-rate, steps or sleep data point from the Google Health API (all of which the API reports with a UTC timestamp)
- **THEN** celia converts it to America/Mexico_City before storing it as `recorded_at`, so its calendar day matches the user's own local day

#### Scenario: Daily resting heart rate is a plain date, not a timestamp
- **WHEN** celia retrieves a daily-resting-heart-rate data point, which the Google Health API reports as a date with no time-of-day component
- **THEN** celia stores that date as-is, since there is no time-of-day to convert
