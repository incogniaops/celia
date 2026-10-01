# Proposal

## Why

The user wants to redesign the dashboard's top biometric-card row: drop the two heart-rate cards, add BMI and a metabolic-age-vs-chronological-age comparison, reorder the rest, and move the glucose average/%CV figures up alongside the A1C card instead of leaving them only inside the "Time in range" article below.

## What Changes

- Remove the Heart Rate and Daily Resting Heart Rate cards.
- Add a BMI card, computed from the current weight and the user's height (a fixed personal constant, like the project's existing fixed America/Mexico_City timezone -- not an ingested data point, since no current source provides height).
- Add a "Metabolic age vs real age" card: metabolic age from the Wyze scale (already ingested, not previously displayed), chronological age computed from the user's birth date (another fixed personal constant).
- Reorder the row to: BMI, metabolic/real age, weight, muscle mass, body fat, glucose average/%CV, A1C.
- Move the average glucose/%CV figures out of the "Time in range" article's text and into their own top card (the A1C card already made the same move for GMI in `a1c-detail-view`); "Time in range" keeps only the five-band breakdown table.

## Capabilities

### Modified Capabilities
- `dashboard`: the biometric-profile requirement's card set, order and source metrics change.

## Impact

- **Changed code**: `app/config.py` (`Settings` gains `profile_height_m`/`profile_birth_date`, read from the new `PROFILE_HEIGHT_M`/`PROFILE_BIRTH_DATE` environment variables -- see design.md for why this replaced an initially-proposed hardcoded module), `app/dashboard_data.py` (`BIOMETRIC_METRIC_TYPES` drops heart-rate types, adds `metabolic_age`; new `get_bmi`/`get_age_comparison` functions taking height/birth date as parameters), `app/routers/dashboard.py` (inject `Settings` and wire the two new values into context), `app/templates/dashboard_content.html` (explicit, ordered cards replacing the generic metric-type loop).
- **No database changes.** `heart_rate`/`daily_resting_heart_rate` keep syncing into `health_metrics` as before (health-metrics-sync is unaffected) -- they're just no longer shown on the dashboard.
- **A new kind of fixed personal constant** (height, birth date), alongside the project's existing fixed `America/Mexico_City` timezone constant -- a deliberate, narrow exception to "no manual data entry", for static personal facts no ingestion source provides, not an ongoing log.
