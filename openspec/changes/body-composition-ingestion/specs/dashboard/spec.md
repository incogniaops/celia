# Spec Delta

## MODIFIED Requirements

### Requirement: Consolidated, time-aligned view
The system SHALL show glucose readings as a trend line, with insulin/carbohydrate markers aligned to the same timeline, a medication-adherence calendar (one row per medication, one column per day in the selected range, a status per cell) for the selected range, and the current biometric profile (weight, body fat, heart rate, resting heart rate, muscle mass) and an estimated A1C (GMI) shown alongside it, each as its own card.

#### Scenario: Data from at least one source is available
- **WHEN** the user opens the dashboard and at least one source has ingested data
- **THEN** glucose readings are shown as a trend line, with insulin/carbohydrate markers aligned to the same timeline, a medication-adherence calendar for the selected range, and the current biometric profile and estimated A1C shown alongside it

#### Scenario: A medication taken more than once a day is consolidated to one status per day
- **WHEN** a medication has more than one scheduled dose on the same day (e.g. twice daily) and at least one of that day's doses is `rejected`
- **THEN** the calendar shows that day as not fully adhered to for that medication, rather than showing a separate row per scheduled time (a deliberate simplification from MyTherapy's own report, which does show one row per time)

#### Scenario: A medication has no dose scheduled on a given day
- **WHEN** a medication in the calendar has no recorded dose for a particular day in the range
- **THEN** that day's cell is shown as empty/not-applicable, distinct from a `confirmed` or `rejected` status

#### Scenario: Muscle mass data is available
- **WHEN** at least one muscle-mass data point has been ingested
- **THEN** a muscle mass card is shown alongside the other biometric cards, with the same "most recent value" behaviour as weight, body fat, heart rate and resting heart rate

### Requirement: Time-in-range and glucose-control summary
The system SHALL show, for the selected range, the percentage of glucose readings falling in each of the five standard AGP bands (very low <54 mg/dL, low 54-69 mg/dL, in range 70-180 mg/dL, high 181-250 mg/dL, very high >250 mg/dL), the average glucose and the glucose coefficient of variation (%CV). The Glucose Management Indicator (GMI, an estimated A1c) is shown as its own card alongside the biometric profile, not repeated here.

#### Scenario: Readings exist in the selected range
- **WHEN** the user opens the dashboard and glucose readings exist in the selected range
- **THEN** the summary shows the percentage of readings in each of the five bands, the average glucose and %CV for that range, and the estimated A1C (GMI) card is shown alongside the biometric profile rather than in this summary

#### Scenario: No glucose readings in the selected range
- **WHEN** no glucose readings exist in the selected range
- **THEN** the summary is omitted rather than shown with misleading zero or undefined values, and the estimated A1C card is also omitted
