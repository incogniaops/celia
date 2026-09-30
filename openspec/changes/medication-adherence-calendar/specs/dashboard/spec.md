# Spec Delta

## MODIFIED Requirements

### Requirement: Consolidated, time-aligned view
The system SHALL show glucose readings as a trend line, with insulin/carbohydrate markers aligned to the same timeline, a medication-adherence calendar (one row per medication, one column per day in the selected range, a status per cell) for the selected range, and the current biometric profile (weight, body fat, heart rate, resting heart rate) shown alongside it.

#### Scenario: Data from at least one source is available
- **WHEN** the user opens the dashboard and at least one source has ingested data
- **THEN** glucose readings are shown as a trend line, with insulin/carbohydrate markers aligned to the same timeline, a medication-adherence calendar for the selected range, and the current biometric profile shown alongside it

#### Scenario: A medication taken more than once a day is consolidated to one status per day
- **WHEN** a medication has more than one scheduled dose on the same day (e.g. twice daily) and at least one of that day's doses is `rejected`
- **THEN** the calendar shows that day as not fully adhered to for that medication, rather than showing a separate row per scheduled time (a deliberate simplification from MyTherapy's own report, which does show one row per time — see design.md)

#### Scenario: A medication has no dose scheduled on a given day
- **WHEN** a medication in the calendar has no recorded dose for a particular day in the range
- **THEN** that day's cell is shown as empty/not-applicable, distinct from a `confirmed` or `rejected` status
