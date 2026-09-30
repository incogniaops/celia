# Tasks

- [x] 1. Add `get_glucose_summary_stats(db, start, end)` to `app/dashboard_data.py`: fetch the same readings as `get_glucose_trend`, compute band percentages (very low/low/in range/high/very high using the `(54, 70, 180, 250)` thresholds), mean, GMI and %CV; return `None` if there are no readings in the range.
- [x] 2. Add `get_agp_percentile_bands(db, start, end)` to `app/dashboard_data.py`: bucket readings by time-of-day rounded to 15 minutes, compute p5/p25/median/p75/p95 per bucket via `statistics.quantiles`; return `None` if readings span fewer than 2 distinct calendar days.
- [x] 3. Add `get_monthly_glucose_calendar(db, start, end)` to `app/dashboard_data.py`: compute each day's average glucose and band, laid out as a list of weeks (Monday-first), each a list of 7 `{date, avg, band} | None` slots.
- [x] 4. Unit tests for all three functions: band-boundary edge cases (values exactly at 54/70/180/250), GMI/%CV against the report's own worked example (112 mg/dL mean -> 6.0% GMI), AGP's <2-days-of-data `None` case, and the calendar's week-alignment/no-data-cell cases.
- [x] 5. Wire the three functions into `app/routers/dashboard.py`'s `_dashboard_context`.
- [x] 6. Add three new sections to `app/templates/dashboard_content.html`: the time-in-range/GMI/%CV summary card, the AGP band chart (new Chart.js canvas, five datasets), and the monthly calendar grid -- using Pico.css defaults plus small inline `style` colouring only, no new stylesheet.
- [x] 7. Integration test: dashboard route renders all three new sections for a known slice of real-shaped glucose data, and omits them gracefully when there isn't enough data (empty range, single-day range).
- [x] 8. Verify end-to-end against the real glucose dataset in the Podman container: compare the rendered time-in-range percentages, GMI and calendar cell values against the user's own LibreView PDF for the same date range (17-30 September 2026) as a sanity check.
- [x] 9. Run `/changelogger` then `/commit` once verified.
