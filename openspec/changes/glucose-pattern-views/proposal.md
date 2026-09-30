# Proposal

## Why

The user reviewed their own real LibreView AGP report (`data/abbott/RodrigoÁlvarez_30-09-2026.pdf`) as a design reference for how they want to see their glucose data. The current dashboard shows only a raw per-reading trend line — it can't answer "what does a typical day look like", "what % of the time am I in range", or "which days this month were rough", all of which the LibreView report answers well and the user explicitly chose to adopt.

## What Changes

- Add a **time-in-range and glucose-control summary**: percentage of readings in each of the five standard AGP bands (very low / low / in range / high / very high), average glucose, GMI (estimated A1c) and %CV, for the selected range.
- Add an **AGP pattern chart**: a "typical day" view overlaying every day in the selected range onto one 24-hour axis, as percentile bands (5th–95th, 25th–75th, median) rather than raw points — alongside the existing raw trend line, not replacing it (the raw trend is still needed for the existing insulin/carbohydrate marker alignment).
- Add a **monthly glucose calendar**: a literal week-row/weekday-column calendar (like LibreView's own "Resumen mensual" page), one cell per day showing that day's average glucose, coloured by the same band it falls into.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `dashboard`: adds three new requirements (time-in-range summary, AGP pattern chart, monthly glucose calendar). The existing "Consolidated, time-aligned view" requirement (raw trend line + markers + medication calendar + biometric profile) is unchanged — these are additions alongside it, not replacements.

## Impact

- **Changed code**: `app/dashboard_data.py` (three new query/aggregation functions), `app/routers/dashboard.py` (wire new data into context), `app/templates/dashboard_content.html` (three new sections).
- **No database changes** — all three views are read-only aggregations over the existing `glucose_readings` table.
- **New stdlib usage**: Python's `statistics` module (`mean`, `stdev`, `quantiles`) for GMI/%CV/AGP percentiles — no new dependency.
- **Fixed clinical thresholds, not user-configurable**: the five AGP bands (<54, 54–69, 70–180, 181–250, >250 mg/dL) are the international AGP consensus bands LibreView itself uses for this report — not the device's personal alarm thresholds (which are a different, user-configurable setting shown on the report's "Detalles del dispositivo" page and out of scope here).
