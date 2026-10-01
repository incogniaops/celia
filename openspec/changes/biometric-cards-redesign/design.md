# Design

## Context

The top card row currently renders from a generic loop over `get_current_biometric_profile`'s result (`BIOMETRIC_METRIC_TYPES = ("weight", "body_fat", "heart_rate", "daily_resting_heart_rate", "muscle_mass")`), in whatever order the DB query returns (alphabetical by `metric_type`). The user wants an explicit, specific order instead, with two new derived cards (BMI, metabolic-vs-chronological age) that need a fixed height and birth date -- two personal facts no current ingestion source provides.

## Goals / Non-Goals

**Goals:**
- Exact card order: BMI, metabolic/real age, weight, muscle mass, body fat, glucose average/%CV, A1C.
- Compute BMI and chronological age from fixed personal constants, not a new ingestion source.
- Remove duplication: glucose average/%CV moves from the "Time in range" article's text into its own top card (the same move `a1c-detail-view` already made for GMI).

**Non-Goals:**
- Letting the user edit height/birth date through the UI -- these are one-time constants in code, like the project's existing fixed `America/Mexico_City` timezone, not a settings feature.
- Removing `heart_rate`/`daily_resting_heart_rate` from `health-metrics-sync` itself -- they keep syncing and being stored, simply no longer shown on the dashboard (someone could still query `health_metrics` directly, or a future change could bring them back).

## Decisions

**Height and birth date are environment variables on `Settings` (`PROFILE_HEIGHT_M`, `PROFILE_BIRTH_DATE`), not a hardcoded module.** The first implementation attempt used a tiny `app/profile.py` module with these as literal constants, mirroring `app/timezone.py`'s fixed-constant pattern -- but unlike the timezone (a public, non-identifying fact), a real birth date and height are personal data that would have been committed in plaintext to this repo's public git history. The user caught this before the commit and asked for environment variables instead, the same place `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` already live specifically because they must never be committed. `get_bmi`/`get_age_comparison` take `height_m`/`birth_date` as explicit parameters rather than importing a constant, so the dashboard router (which already depends on `Settings` via `Depends(get_settings)`, same as `sync.py`) passes them through.

**BMI is computed by celia itself from weight / height^2, not read from Wyze's own stored `bmi` metric_type.** The Wyze export already includes a `bmi` field (see `body-composition-ingestion`), computed by the Wyze app from whatever height is configured there. Computing it independently in celia, from the user-confirmed height, makes the figure auditable in celia's own code rather than trusting a third-party app's height setting and rounding. The stored Wyze `bmi` metric_type is simply unused by the dashboard, same as the other not-yet-displayed body-composition fields.

**Chronological age is computed from `BIRTH_DATE` and the current America/Mexico_City date** (reusing `app.timezone.MEXICO_CITY`, the same "what day is it" the rest of the app already uses), not server-local time -- consistent with `mexico-city-local-time`.

**`get_bmi`/`get_age_comparison` take the already-fetched `biometric_profile` dict, not a new database query.** `get_current_biometric_profile` already fetches `weight` and (once added) `metabolic_age`; these two new functions are pure computations over that same dict, avoiding a redundant query.

**The generic metric-type loop is replaced with explicit per-card template blocks**, each independently guarded (`{% if %}`) by whether its underlying data exists -- matches the existing pattern the A1C card already uses, rather than extending the generic loop with special-cased ordering logic that would be harder to follow than just writing the seven cards out directly.

## Risks / Trade-offs

- **A future second user, or a house move, would need a code change to update height/birth date/timezone** -- accepted, consistent with this project's existing single-user, single-location scope (see `mexico-city-local-time`'s own equivalent trade-off).
- **BMI could, in principle, disagree slightly with Wyze's own stored value** if Wyze's configured height differs from the real one -- that's exactly the discrepancy this change resolves by computing it independently.
