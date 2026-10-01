# Spec Delta

## MODIFIED Requirements

### Requirement: Time-in-range and glucose-control summary
The system SHALL show, for the selected range, the percentage of glucose readings falling in each of the five standard AGP bands (very low <54 mg/dL, low 54-69 mg/dL, in range 70-180 mg/dL, high 181-250 mg/dL, very high >250 mg/dL), the average glucose and the glucose coefficient of variation (%CV). The Glucose Management Indicator (GMI, an estimated A1c) is shown as its own card alongside the biometric profile, not repeated here, in both percentage and mmol/mol (IFCC units), together with how many of the selected range's calendar days actually have at least one glucose reading, out of the total days in the range.

#### Scenario: Readings exist in the selected range
- **WHEN** the user opens the dashboard and glucose readings exist in the selected range
- **THEN** the summary shows the percentage of readings in each of the five bands, the average glucose and %CV for that range, and the estimated A1C card shows the GMI in both percentage and mmol/mol, plus how many of the range's calendar days have at least one reading, out of the total days in the range

#### Scenario: No glucose readings in the selected range
- **WHEN** no glucose readings exist in the selected range
- **THEN** the summary is omitted rather than shown with misleading zero or undefined values, and the estimated A1C card is also omitted
