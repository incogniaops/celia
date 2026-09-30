# Dashboard

## Purpose
Show glucose, meals, insulin, medication adherence, biometric profile and sensor-log data together on one responsive screen, for a chosen date range, so the user can understand his own patterns and prepare for a doctor's appointment.

Source of truth: `docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md`, US-04.

## Requirements

### Requirement: Consolidated, time-aligned view
The system SHALL show glucose readings as a trend line, with meal, insulin and medication-adherence markers aligned to the same timeline, and the current biometric profile (weight, body fat, heart rate, resting heart rate) shown alongside it.

#### Scenario: Data from at least one source is available
- **WHEN** the user opens the dashboard and at least one source has ingested data
- **THEN** glucose readings are shown as a trend line, with meal, insulin and medication-adherence markers aligned to the same timeline, and the current biometric profile shown alongside it

### Requirement: Date-range filtering
The system SHALL show only data within a date range the user selects.

#### Scenario: User selects a date range
- **WHEN** the user selects a date range
- **THEN** the dashboard refreshes to show only data within that range

### Requirement: Responsive layout
The system SHALL adapt its layout to the screen size, remaining usable without horizontal scrolling of the main chart, on both desktop and mobile browsers.

#### Scenario: Opened from a mobile browser
- **WHEN** the dashboard is opened from a desktop browser or a mobile browser
- **THEN** the layout adapts to the screen size and remains usable without horizontal scrolling of the main chart

### Requirement: Empty state
The system SHALL explain how to add data when none has been ingested yet.

#### Scenario: No data ingested yet
- **WHEN** the user opens the dashboard and no data has been ingested yet
- **THEN** an empty state explains how to upload a Libre export, upload a MyTherapy report, or connect Google Health
