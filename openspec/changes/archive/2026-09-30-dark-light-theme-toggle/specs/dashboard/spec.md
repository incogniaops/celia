# Spec Delta

## ADDED Requirements

### Requirement: Dark/light theme toggle
The system SHALL let the user switch between a dark and a light theme, defaulting to dark when no preference has been stored, and SHALL remember the choice across page loads.

#### Scenario: First visit, no stored preference
- **WHEN** the user opens the dashboard with no theme preference stored in their browser
- **THEN** the dark theme is shown

#### Scenario: User toggles the theme
- **WHEN** the user clicks the theme toggle
- **THEN** the page switches to the other theme immediately, and the choice is remembered for future visits in that browser

#### Scenario: Returning with a stored preference
- **WHEN** the user has previously chosen light (or dark) and opens the dashboard again
- **THEN** that theme is shown from the start, without a flash of the other theme first

#### Scenario: Charts and hardcoded-colour cells stay legible under either theme
- **WHEN** the user views the glucose trend chart, the ambulatory glucose profile chart, the "Time in range" table, or the "Monthly glucose calendar", in either dark or light theme
- **THEN** chart axis labels, legend text and gridlines render in a colour legible against the current theme's background, and the pastel-background table/calendar cells keep readable text regardless of theme

#### Scenario: Toggling theme without changing the date range
- **WHEN** the user clicks the theme toggle without triggering an HTMX range-preset swap
- **THEN** the glucose trend chart and the ambulatory glucose profile chart redraw immediately with colours matching the new theme, rather than keeping the previous theme's colours until the next range-preset click
