# Spec Delta

## MODIFIED Requirements

### Requirement: Responsive layout
The system SHALL adapt its layout to the screen size, remaining usable without horizontal scrolling of the main chart, on both desktop and mobile browsers. Charts SHALL reliably fill their container after an HTMX swap (for example, selecting a date-range preset), not intermittently render at a fixed small size.

#### Scenario: Opened from a mobile browser
- **WHEN** the dashboard is opened from a desktop browser or a mobile browser
- **THEN** the layout adapts to the screen size and remains usable without horizontal scrolling of the main chart

#### Scenario: Selecting a date-range preset after the page has already loaded
- **WHEN** the user selects a date-range preset, swapping in a new chart via HTMX
- **THEN** the chart reliably fills its container's actual size, not a fixed fallback size from measuring before the swapped-in layout had settled
