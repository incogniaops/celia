# Dashboard

## Purpose
Show glucose, meals, insulin, medication adherence, biometric profile and sensor-log data together on one responsive screen, for a chosen date range, so the user can understand his own patterns and prepare for a doctor's appointment.

Source of truth: `docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md`, US-04.

## Requirements

### Requirement: Consolidated, time-aligned view
The system SHALL show glucose readings as a trend line, with insulin/carbohydrate markers aligned to the same timeline, a medication-adherence calendar (one row per medication, one column per day in the selected range, a status per cell) for the selected range, and a biometric-and-glucose-summary card row alongside it, in this order: metabolic age delta, weight, body fat, BMI, glucose average (with %CV shown alongside it), and estimated A1C (GMI) -- each as its own card. Muscle mass is not shown as a card (though it continues to be ingested and stored).

#### Scenario: Data from at least one source is available
- **WHEN** the user opens the dashboard and at least one source has ingested data
- **THEN** glucose readings are shown as a trend line, with insulin/carbohydrate markers aligned to the same timeline, a medication-adherence calendar for the selected range, and the biometric-and-glucose-summary card row shown alongside it, in the specified order

#### Scenario: A medication taken more than once a day is consolidated to one status per day
- **WHEN** a medication has more than one scheduled dose on the same day (e.g. twice daily) and at least one of that day's doses is `rejected`
- **THEN** the calendar shows that day as not fully adhered to for that medication, rather than showing a separate row per scheduled time (a deliberate simplification from MyTherapy's own report, which does show one row per time — see design.md)

#### Scenario: A medication has no dose scheduled on a given day
- **WHEN** a medication in the calendar has no recorded dose for a particular day in the range
- **THEN** that day's cell is shown as empty/not-applicable, distinct from a `confirmed` or `rejected` status

#### Scenario: BMI is computed from weight and a fixed height
- **WHEN** a current weight value is available
- **THEN** the BMI card shows weight divided by the square of the user's height (a fixed personal constant, not an ingested data point, since no current source provides height)

#### Scenario: Metabolic age is available from the Wyze scale
- **WHEN** at least one metabolic-age data point has been ingested (from the Wyze body-composition export)
- **THEN** the metabolic age delta card shows the metabolic age minus the chronological age computed from the user's fixed birth date, as a single signed number -- never the chronological age itself, so the dashboard never reveals the user's real age even indirectly

#### Scenario: No metabolic age data is available
- **WHEN** no metabolic-age data point has been ingested
- **THEN** the metabolic age delta card is omitted, rather than showing a delta against a missing value

#### Scenario: Heart rate and resting heart rate are no longer shown
- **WHEN** the user opens the dashboard
- **THEN** no Heart Rate or Daily Resting Heart Rate card is shown, even though both continue to be synced and stored as before

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

#### Scenario: Dashboard opened without a selected range, late in the local evening
- **WHEN** the user opens the dashboard without selecting a range, at a local time of day where UTC's calendar date has already rolled over to the next day
- **THEN** the default range's "today" is still the user's own America/Mexico_City calendar day, not UTC's

### Requirement: Responsive layout
The system SHALL adapt its layout to the screen size, remaining usable without horizontal scrolling of the main chart, on both desktop and mobile browsers. Charts SHALL reliably fill their container after an HTMX swap (for example, selecting a date-range preset), not intermittently render at a fixed small size.

#### Scenario: Opened from a mobile browser
- **WHEN** the dashboard is opened from a desktop browser or a mobile browser
- **THEN** the layout adapts to the screen size and remains usable without horizontal scrolling of the main chart

#### Scenario: Selecting a date-range preset after the page has already loaded
- **WHEN** the user selects a date-range preset, swapping in a new chart via HTMX
- **THEN** the chart reliably fills its container's actual size, not a fixed fallback size from measuring before the swapped-in layout had settled

### Requirement: Empty state
The system SHALL explain how to add data when none has been ingested yet.

#### Scenario: No data ingested yet
- **WHEN** the user opens the dashboard and no data has been ingested yet
- **THEN** an empty state explains how to upload a Libre export, upload a MyTherapy report, or connect Google Health

### Requirement: Biometric profile source precedence
The system's "current biometric profile" (weight, body fat, heart rate, resting heart rate) SHALL show the most recently recorded value in `health_metrics` for each metric type, with no explicit precedence between sources when more than one stores the same metric type -- weight, body fat and heart rate are each stored by both Google Health and the Wyze body-composition export, and the more recent reading wins regardless of which one produced it, since both represent real readings of the same physical measurement. Resting heart rate has only ever had one source (Google Health; the Wyze export's own "Heart Rate" section is a plain heart rate, not a daily resting figure). MyTherapy's weight/activity data remains the one source genuinely absent, not merely deprioritised: medication-ingestion deliberately does not persist MyTherapy's `activity`/`measurement` rows, so there is nothing from that source to compete with Google Health or Wyze.

#### Scenario: Weight, body fat or heart rate is available from both Google Health and Wyze
- **WHEN** both a Google Health-sourced and a Wyze-sourced reading exist for the same metric type (weight, body fat or heart rate)
- **THEN** the dashboard shows whichever reading has the more recent `recorded_at`, with no preference for one source over the other

#### Scenario: MyTherapy's weight/activity data remains absent, not merely deprioritised
- **WHEN** the user views the current biometric profile
- **THEN** no MyTherapy-sourced value competes with Google Health or Wyze for weight, body fat, heart rate or resting heart rate, because medication-ingestion deliberately does not persist MyTherapy's `activity`/`measurement` rows

#### Scenario: BR-06 becomes live if MyTherapy weight/steps are ever persisted
- **WHEN** a future change starts persisting MyTherapy's `activity`/`measurement` rows (reversing medication-ingestion's current Non-Goal)
- **THEN** the dashboard's biometric-profile query must decide how MyTherapy's data weighs against the existing most-recent-wins rule already used between Google Health and Wyze, rather than assuming MyTherapy is still absent

### Requirement: Time-in-range and glucose-control summary
The system SHALL show, for the selected range, the percentage of glucose readings falling in each of the five standard AGP bands (very low <54 mg/dL, low 54-69 mg/dL, in range 70-180 mg/dL, high 181-250 mg/dL, very high >250 mg/dL). The average glucose, the glucose coefficient of variation (%CV) and the Glucose Management Indicator (GMI, an estimated A1c, as a percentage with the mmol/mol equivalent on its own line below it) are each shown as their own card in the biometric-and-glucose-summary row, not repeated here. `a1c-detail-view`'s data-coverage detail (days with data out of days in range) is still computed but no longer shown on the card.

#### Scenario: Readings exist in the selected range
- **WHEN** the user opens the dashboard and glucose readings exist in the selected range
- **THEN** the summary shows the percentage of readings in each of the five bands for that range, and the average glucose, %CV and estimated A1C are each shown as their own card in the biometric-and-glucose-summary row instead

#### Scenario: No glucose readings in the selected range
- **WHEN** no glucose readings exist in the selected range
- **THEN** the summary is omitted rather than shown with misleading zero or undefined values, and the average/%CV and A1C cards are also omitted

### Requirement: Ambulatory glucose profile (AGP) pattern chart
The system SHALL show an AGP pattern chart: every day in the selected range overlaid onto a single 24-hour axis as percentile bands (5th-95th percentile, 25th-75th percentile, and median), so the user can see a "typical day" pattern independently of the raw per-reading trend line.

#### Scenario: Multiple days of readings exist in the selected range
- **WHEN** the user opens the dashboard and glucose readings from more than one day exist in the selected range
- **THEN** the AGP chart shows the 5th-95th percentile band, the 25th-75th percentile band and the median, each computed per time-of-day across all days in the range

#### Scenario: Fewer than two days of data
- **WHEN** the selected range contains readings from zero or one calendar day
- **THEN** the AGP chart is omitted, since a percentile band across a single day is not meaningful

### Requirement: Monthly glucose calendar
The system SHALL show a calendar-grid view (week rows, Monday-to-Sunday columns, day-of-month numbers) for the selected range, with one cell per day showing that day's average glucose, coloured by the band (as defined in the time-in-range summary) its average falls into.

#### Scenario: A day has glucose readings
- **WHEN** a day within the selected range has at least one glucose reading
- **THEN** its calendar cell shows that day's average glucose, coloured by its band

#### Scenario: A day has no glucose readings
- **WHEN** a day within the selected range has no glucose readings
- **THEN** its calendar cell is shown empty, distinct from a day with an in-range average

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
