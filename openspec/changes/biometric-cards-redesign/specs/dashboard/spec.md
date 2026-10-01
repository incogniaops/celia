# Spec Delta

## MODIFIED Requirements

### Requirement: Consolidated, time-aligned view
The system SHALL show glucose readings as a trend line, with insulin/carbohydrate markers aligned to the same timeline, a medication-adherence calendar (one row per medication, one column per day in the selected range, a status per cell) for the selected range, and a biometric-and-glucose-summary card row alongside it, in this order: metabolic age delta, weight, body fat, BMI, glucose average/%CV, and estimated A1C (GMI) -- each as its own card. Muscle mass is not shown as a card (though it continues to be ingested and stored).

#### Scenario: Data from at least one source is available
- **WHEN** the user opens the dashboard and at least one source has ingested data
- **THEN** glucose readings are shown as a trend line, with insulin/carbohydrate markers aligned to the same timeline, a medication-adherence calendar for the selected range, and the biometric-and-glucose-summary card row shown alongside it, in the specified order

#### Scenario: A medication taken more than once a day is consolidated to one status per day
- **WHEN** a medication has more than one scheduled dose on the same day (e.g. twice daily) and at least one of that day's doses is `rejected`
- **THEN** the calendar shows that day as not fully adhered to for that medication, rather than showing a separate row per scheduled time (a deliberate simplification from MyTherapy's own report, which does show one row per time)

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

### Requirement: Time-in-range and glucose-control summary
The system SHALL show, for the selected range, the percentage of glucose readings falling in each of the five standard AGP bands (very low <54 mg/dL, low 54-69 mg/dL, in range 70-180 mg/dL, high 181-250 mg/dL, very high >250 mg/dL). The average glucose, the glucose coefficient of variation (%CV) and the Glucose Management Indicator (GMI, an estimated A1c, as a percentage with the mmol/mol equivalent on its own line below it) are each shown as their own card in the biometric-and-glucose-summary row, not repeated here. `a1c-detail-view`'s data-coverage detail (days with data out of days in range) is still computed but no longer shown on the card.

#### Scenario: Readings exist in the selected range
- **WHEN** the user opens the dashboard and glucose readings exist in the selected range
- **THEN** the summary shows the percentage of readings in each of the five bands for that range, and the average glucose, %CV and estimated A1C are each shown as their own card in the biometric-and-glucose-summary row instead

#### Scenario: No glucose readings in the selected range
- **WHEN** no glucose readings exist in the selected range
- **THEN** the summary is omitted rather than shown with misleading zero or undefined values, and the average/%CV and A1C cards are also omitted
