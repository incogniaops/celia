# Spec Delta

## MODIFIED Requirements

### Requirement: Date-range filtering
The system SHALL show only data within a date range the user selects. When no range is selected, the default range's "today" boundary SHALL be computed in America/Mexico_City local time, not UTC, so the default range matches the user's own calendar day regardless of the time of day the dashboard is opened.

#### Scenario: User selects a date range
- **WHEN** the user selects a date range
- **THEN** the dashboard refreshes to show only data within that range

#### Scenario: Dashboard opened without a selected range, late in the local evening
- **WHEN** the user opens the dashboard without selecting a range, at a local time of day where UTC's calendar date has already rolled over to the next day
- **THEN** the default range's "today" is still the user's own America/Mexico_City calendar day, not UTC's
