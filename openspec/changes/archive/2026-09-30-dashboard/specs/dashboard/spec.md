# Spec Delta

## ADDED Requirements

### Requirement: Biometric profile source precedence is currently trivial, not absent
The system's "current biometric profile" (weight, body fat, heart rate, resting heart rate) SHALL be read from `health_metrics` (Google Health) only, since medication-ingestion deliberately does not persist MyTherapy's `activity`/`measurement` rows (including weight) — there is no second stored source to prefer over. This is BR-06 applied to the system as actually built, not BR-06 left unimplemented.

#### Scenario: Weight shown on the dashboard has one source today
- **WHEN** the user views the current biometric profile
- **THEN** the weight, body-fat, heart-rate and resting-heart-rate values shown come from `health_metrics`, because no MyTherapy weight/steps rows exist anywhere in the database to compete with them

#### Scenario: BR-06 becomes live if MyTherapy weight/steps are ever persisted
- **WHEN** a future change starts persisting MyTherapy's `activity`/`measurement` rows (reversing medication-ingestion's current Non-Goal)
- **THEN** the dashboard's biometric-profile query must be revisited to actually choose between the two sources per BR-06, rather than assuming `health_metrics` is the only one
