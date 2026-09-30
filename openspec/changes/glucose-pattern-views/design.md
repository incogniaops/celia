# Design

## Context

The user's real LibreView AGP report (`data/abbott/RodrigoÁlvarez_30-09-2026.pdf`) shows three distinct patterns for the same underlying glucose data that `glucose_readings` already has: a time-in-range/GMI summary card, an AGP percentile-band chart, and a literal monthly calendar. All three are read-only aggregations over existing data — no ingestion changes needed.

`get_glucose_trend` (`app/dashboard_data.py`) already selects `GLUCOSE_RECORD_TYPES = (0, 1)` (historic + manual scan) in a date range, with `historic_glucose_mgdl` or `scan_glucose_mgdl` as the value — the same source these three new functions reuse.

## Goals / Non-Goals

**Goals:**
- Add the three views the user chose, reusing the existing glucose data and the existing date-range control — no new upload/ingestion work.
- Use only the Python standard library for the statistics (`statistics.mean`, `statistics.stdev`, `statistics.quantiles`) — no new dependency for something this repo's data volumes don't need a library for.
- Keep the AGP chart additive, not a replacement for the raw trend line, since the raw trend is where insulin/carbohydrate markers are aligned (existing requirement, unchanged by this proposal).

**Non-Goals:**
- Meal-pattern breakdown (before/after-meal averages by time-of-day bucket) and the "Resumen semanal"/"Registro diario" day-by-day annotated views from the same PDF — not chosen by the user this round; a future change if wanted.
- User-configurable band thresholds or device alarm settings — the five AGP bands are fixed clinical consensus values, matching the report exactly, not the personal device alarm configuration shown on the report's "Detalles del dispositivo" page.
- Per-day AGP (the report's "Registro diario" per-day charts) — the AGP requirement here is specifically the multi-day percentile-band overlay, not a day-by-day gallery.

## Decisions

**AGP band thresholds are hardcoded module constants** in `app/dashboard_data.py`, mirroring `GLUCOSE_RECORD_TYPES`/`BIOMETRIC_METRIC_TYPES`'s existing pattern: `(54, 70, 180, 250)` as the four boundaries producing five bands (very low / low / in range / high / very high). These are the same values visible in the user's own report's "Tiempo en los rangos" panel and are a fixed international AGP consensus, not configuration.

**GMI formula**: `GMI(%) = 3.31 + 0.02392 * mean_mgdl` (Bergenstal et al., *Diabetes Care* 2018) — the same formula LibreView's own report uses, confirmed by the report's stated 112 mg/dL average producing 6.0% GMI (`3.31 + 0.02392*112 = 6.0`). No alternative formula considered; this is what the source-of-truth report shows.

**%CV**: `stdev / mean * 100` over the same readings, matching the report's "Variabilidad de glucosa" figure (16.3% in the report at a 112 mg/dL mean — order-of-magnitude consistent with `statistics.stdev` over the underlying 15-minute-cadence readings).

**Time-in-range summary omitted with <1 reading** (empty range) rather than shown with a 0%-everywhere or divide-by-zero result — mirrors the existing "no medication doses in this range" empty-state pattern already used elsewhere in the template.

**AGP percentile bucketing**: group every glucose reading in the range by time-of-day rounded to the nearest 15 minutes (96 buckets/day) — this matches the FreeStyle Libre's own ~15-minute historic-reading cadence, so each bucket aggregates one reading per day rather than interpolating. For each of the 96 buckets, compute p5/p25/median/p75/p95 via `statistics.quantiles(data, n=100, method="inclusive")`, picking the relevant indices (or `statistics.median` for p50) -- skipping (`None`) any bucket with fewer than 2 distinct days of data, since a percentile band across 1 data point isn't meaningful. Requires at least 2 distinct calendar days of readings in the range overall, per the spec's second AGP scenario, or the whole chart is omitted.

**AGP rendering**: Chart.js, five line datasets over a 96-point 24-hour x-axis (labelled every hour) — p5 and p95 as the outer band (`fill: '+1'`/`'-1'` between adjacent datasets, low opacity), p25/p75 as the inner band (higher opacity), median as a solid line — the same "band of bands" visual as the report's own AGP chart, built from existing per-point line datasets rather than a new chart type/library.

**Monthly glucose calendar layout**: a literal calendar grid (week rows, Monday-first weekday columns), not the medication-adherence calendar's row-per-item/column-per-day table — these look different because the *questions* they answer differ: "how did each medication do over the range" (row-per-med) versus "how did each individual day look, in its natural calendar position" (grid). Built as a Python-side list-of-weeks structure (each week a list of 7 `{date, avg, band} | None` slots, `None` for days outside the selected range that share a week with in-range days), so the template only has to render rows of cells.

**Colour mapping for calendar cells and the time-in-range bands**: reuse Pico.css's existing semantic colour vocabulary (no new palette, consistent with the earlier "solo el calendario" decision) — in-range cells get no special colour (plain), low/very-low get a subtle red-tinted background, high/very-high get a subtle amber-tinted background, via small inline `style` attributes rather than a new stylesheet.

## Risks / Trade-offs

- **15-minute bucketing assumes Libre's own cadence**: if a future data source has a different cadence (e.g. a denser CGM), buckets would just aggregate more readings per bucket — not a correctness problem, just a coarser granularity than the source data in that case. Not addressed further here.
- **Inline `style` colouring vs. a stylesheet**: slightly more verbose in the template than dedicated CSS classes, but avoids introducing new CSS files/rules for three small colour rules, consistent with this project's "no CSS build step" stance.
