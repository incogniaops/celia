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
