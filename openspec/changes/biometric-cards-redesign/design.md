# Design

## Context

The top card row currently renders from a generic loop over `get_current_biometric_profile`'s result (`BIOMETRIC_METRIC_TYPES = ("weight", "body_fat", "heart_rate", "daily_resting_heart_rate", "muscle_mass")`), in whatever order the DB query returns (alphabetical by `metric_type`). The user wants an explicit, specific order instead, with two new derived cards (BMI, metabolic-vs-chronological age) that need a fixed height and birth date -- two personal facts no current ingestion source provides.

## Goals / Non-Goals

**Goals (final state, after the two revisions below):**
- Exact card order: metabolic age delta, weight, body fat, BMI, glucose average, A1C.
- Compute BMI and the age delta from fixed personal facts (height, birth date), not a new ingestion source, and never expose the chronological age itself.
- Remove duplication: glucose average/%CV moves from the "Time in range" article's text into its own top card (the same move `a1c-detail-view` already made for GMI).

**Non-Goals:**
- Letting the user edit height/birth date through the UI -- these are one-time environment variables, like the project's existing fixed `America/Mexico_City` timezone constant, not a settings feature.
- Removing `heart_rate`/`daily_resting_heart_rate`/`muscle_mass` from `health-metrics-sync`/`body-composition-ingestion` themselves -- they keep syncing and being stored, simply no longer shown on the dashboard (someone could still query `health_metrics` directly, or a future change could bring any of them back).

## Decisions

**Height and birth date are environment variables on `Settings` (`PROFILE_HEIGHT_M`, `PROFILE_BIRTH_DATE`), not a hardcoded module.** The first implementation attempt used a tiny `app/profile.py` module with these as literal constants, mirroring `app/timezone.py`'s fixed-constant pattern -- but unlike the timezone (a public, non-identifying fact), a real birth date and height are personal data that would have been committed in plaintext to this repo's public git history. The user caught this before the commit and asked for environment variables instead, the same place `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` already live specifically because they must never be committed. `get_bmi`/`get_age_comparison` take `height_m`/`birth_date` as explicit parameters rather than importing a constant, so the dashboard router (which already depends on `Settings` via `Depends(get_settings)`, same as `sync.py`) passes them through.

**BMI is computed by celia itself from weight / height^2, not read from Wyze's own stored `bmi` metric_type.** The Wyze export already includes a `bmi` field (see `body-composition-ingestion`), computed by the Wyze app from whatever height is configured there. Computing it independently in celia, from the user-confirmed height, makes the figure auditable in celia's own code rather than trusting a third-party app's height setting and rounding. The stored Wyze `bmi` metric_type is simply unused by the dashboard, same as the other not-yet-displayed body-composition fields.

**Chronological age is computed from `BIRTH_DATE` and the current America/Mexico_City date** (reusing `app.timezone.MEXICO_CITY`, the same "what day is it" the rest of the app already uses), not server-local time -- consistent with `mexico-city-local-time`.

**`get_bmi`/`get_age_comparison` take the already-fetched `biometric_profile` dict, not a new database query.** `get_current_biometric_profile` already fetches `weight` and (once added) `metabolic_age`; these two new functions are pure computations over that same dict, avoiding a redundant query.

**The generic metric-type loop is replaced with explicit per-card template blocks**, each independently guarded (`{% if %}`) by whether its underlying data exists -- matches the existing pattern the A1C card already uses, rather than extending the generic loop with special-cased ordering logic that would be harder to follow than just writing the seven cards out directly.

## Revision: muscle mass dropped, BMI reordered, age shown only as a delta

After initial implementation and verification, the user asked for three further adjustments to the same card row:

- **Drop the Muscle Mass card** entirely (still ingested and stored, same treatment already given to heart rate).
- **Move BMI to after Body Fat**, not first. Final order: metabolic age delta, weight, body fat, BMI, glucose average/%CV, A1C.
- **Show only the metabolic-age-vs-real-age *delta*, never either age on its own.** The original "44 vs 47" card displayed the real (chronological) age directly -- exactly the detail `PROFILE_BIRTH_DATE` was introduced to keep out of source control, now also kept off the rendered page itself. `get_age_comparison` was changed to compute and return only `metabolic_age - real_age` (e.g. `-3`), never the real age; the template only ever receives this single signed number, so there is no code path -- not even an unused template variable -- through which the real age could leak into the rendered HTML.

## Revision: card text tidy-up

A further round of user feedback, purely presentational, with no data/logic changes:

- The age-delta card's caption dropped the parenthetical "(not shown)" -- it explained *why* the design omits the real age, but reads as an odd aside once the card itself is self-evidently just a delta; the omission is already documented here in design.md, not something the card's own caption needs to justify.
- "Glucose average / CV" shortened to "Glucose average" as the header -- the card's `<small>` line already reads "CV: X%", so the header didn't need to repeat it.
- The A1C card's mmol/mol figure moved from inline beside the percentage to its own `<small>` line below it (matching the same value/small-caption layout every other card already uses), and the GMI/data-coverage caption lines (`"Glucose Management Indicator (GMI)"`, `"Data spans X of Y days"`) were removed from the card entirely -- `get_glucose_summary_stats` still computes `days_with_data`/`days_in_range` (no change there), simply not rendered.

## Risks / Trade-offs

- **A future second user, or a house move, would need a code change to update height/birth date/timezone** -- accepted, consistent with this project's existing single-user, single-location scope (see `mexico-city-local-time`'s own equivalent trade-off).
- **BMI could, in principle, disagree slightly with Wyze's own stored value** if Wyze's configured height differs from the real one -- that's exactly the discrepancy this change resolves by computing it independently.
