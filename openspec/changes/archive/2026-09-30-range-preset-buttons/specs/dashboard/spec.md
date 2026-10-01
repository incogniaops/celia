# Spec Delta

## MODIFIED Requirements

### Requirement: Date-range filtering
The system SHALL show only data within a date range the user selects, via four fixed presets (last 7, 14, 30 or 90 days ending on the current America/Mexico_City calendar day) rather than manually picked dates. When no range is selected, the default range is the last 30 days. The preset matching the currently-viewed range, if any, SHALL be shown as selected.

#### Scenario: User selects a date range
- **WHEN** the user selects one of the four range presets
- **THEN** the dashboard refreshes immediately to show only data within that range, without a separate confirmation step

#### Scenario: Dashboard opened with no range selected
- **WHEN** the user opens the dashboard without selecting a range
- **THEN** the last-30-days preset is used, and shown as selected

#### Scenario: A non-preset range is viewed
- **WHEN** the dashboard is viewed with a `start`/`end` combination that doesn't match any of the four presets (for example, via a direct URL)
- **THEN** the dashboard still renders that range correctly, with none of the four presets shown as selected
