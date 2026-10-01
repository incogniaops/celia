# Proposal

## Why

The user wants to redesign the dashboard's top biometric-card row: drop the heart-rate and muscle-mass cards, add BMI and a metabolic-age-vs-chronological-age comparison, reorder the rest, and move the glucose average/%CV figures up alongside the A1C card instead of leaving them only inside the "Time in range" article below. This proposal reflects the final shape reached after three rounds of user feedback (see design.md's Context and Revision sections for how each round changed the plan); it is not a record of only the first draft.

## What Changes

- Remove the Heart Rate, Daily Resting Heart Rate and Muscle Mass cards (all three keep syncing/being ingested as before, just no longer shown).
- Add a BMI card, computed by celia itself from the current weight and the user's height (a fixed personal fact, not an ingested data point, since no current source provides height) -- not read from the Wyze export's own stored `bmi` value.
- Add a "Metabolic age delta" card: the Wyze-sourced metabolic age minus the chronological age computed from the user's birth date (another fixed personal fact), shown as a single signed number (e.g. `-3`) -- never either age on its own, so the dashboard never reveals the user's real age even indirectly.
- Height and birth date are read from `PROFILE_HEIGHT_M`/`PROFILE_BIRTH_DATE` environment variables on `Settings`, not committed to source -- an initial hardcoded-module attempt was caught and corrected before committing, since a real birth date and height would otherwise have been published in this repo's git history (see design.md).
- Final card order: metabolic age delta, weight, body fat, BMI, glucose average, A1C.
- Move the average glucose/%CV figures out of the "Time in range" article's text and into their own "Glucose average" top card (the A1C card already made the same move for GMI in `a1c-detail-view`); "Time in range" keeps only the five-band breakdown table.
- Tidy up card text: no "(not shown)" aside on the age-delta card, "Glucose average" (not "Glucose average / CV") as that card's header, and the A1C card's mmol/mol figure on its own small line below the percentage, with the GMI/data-coverage caption lines removed from the card (the underlying figures stay computed, just not rendered).

## Capabilities

### Modified Capabilities
- `dashboard`: the biometric-profile requirement's card set, order and source metrics change.

## Impact

- **Changed code**: `app/config.py` (`Settings` gains `profile_height_m`/`profile_birth_date`, read from the new `PROFILE_HEIGHT_M`/`PROFILE_BIRTH_DATE` environment variables), `app/dashboard_data.py` (`BIOMETRIC_METRIC_TYPES` drops heart-rate types and `muscle_mass`, adds `metabolic_age`; new `get_bmi`/`get_age_comparison` functions, the latter returning only the age delta), `app/routers/dashboard.py` (inject `Settings` and wire `bmi`/`age_comparison` into context), `app/templates/dashboard_content.html` (explicit, ordered cards replacing the generic metric-type loop), `compose.yaml` and `.env.example` (document the two new environment variables), `tests/conftest.py`/`tests/test_google_auth.py`/`tests/test_health_metrics_sync.py` (test-only placeholder values for the two new `Settings` fields).
- **No database changes.** `heart_rate`/`daily_resting_heart_rate`/`muscle_mass` keep syncing into `health_metrics` as before (health-metrics-sync and body-composition-ingestion are unaffected) -- they're just no longer shown on the dashboard.
- **A new kind of fixed personal constant** (height, birth date), alongside the project's existing fixed `America/Mexico_City` timezone constant -- a deliberate, narrow exception to "no manual data entry", for static personal facts no ingestion source provides, not an ongoing log. Unlike the timezone, these two are personal data, so they live only in the gitignored `.env`/environment, never in source.
