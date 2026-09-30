# Spec Delta

## ADDED Requirements

### Requirement: Time-in-range and glucose-control summary
The system SHALL show, for the selected range, the percentage of glucose readings falling in each of the five standard AGP bands (very low <54 mg/dL, low 54-69 mg/dL, in range 70-180 mg/dL, high 181-250 mg/dL, very high >250 mg/dL), the average glucose, the Glucose Management Indicator (GMI, an estimated A1c) and the glucose coefficient of variation (%CV).

#### Scenario: Readings exist in the selected range
- **WHEN** the user opens the dashboard and glucose readings exist in the selected range
- **THEN** the summary shows the percentage of readings in each of the five bands, the average glucose, GMI and %CV for that range

#### Scenario: No glucose readings in the selected range
- **WHEN** no glucose readings exist in the selected range
- **THEN** the summary is omitted rather than shown with misleading zero or undefined values

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
