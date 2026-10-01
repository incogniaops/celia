# Tasks

- [x] 1. Add `app/timezone.py` with `MEXICO_CITY = ZoneInfo("America/Mexico_City")`.
- [x] 2. Update `_parse_google_timestamp` in `app/health_metrics_sync.py` to convert the parsed UTC instant to `MEXICO_CITY` before stripping tzinfo; leave `_extract_daily_resting_heart_rate` untouched (plain date, no time-of-day).
- [x] 3. Unit tests: a known UTC timestamp converts to the correct America/Mexico_City wall-clock time (six hours earlier, no DST complication), and `daily_resting_heart_rate` extraction is unaffected.
- [x] 4. Update `_resolve_range` in `app/routers/dashboard.py` to compute `today` from `MEXICO_CITY`, not `datetime.utcnow()`.
- [x] 5. Unit/integration test: the default range's end boundary reflects the America/Mexico_City calendar day.
- [x] 6. Verify end-to-end in the Podman container: confirmed `zoneinfo.ZoneInfo("America/Mexico_City")` resolves correctly via the actual code path (`_parse_google_timestamp` called directly in the container), triggered a real sync (0 new data, already up to date), and inspected real pre-backfill rows showing the exact bug (`recorded_at` identical to the raw UTC source).
- [x] 7. Ran the one-time backfill against the real dev database, corrected from the plan: the single-statement `UPDATE ... WHERE source_platform != 'wyze_export'` (a) hit a unique-constraint collision on `steps` rows shifting into each other, and (b) the scoping `SELECT` revealed `daily_resting_heart_rate` rows were wrongly included (a plain date, never meant to shift). Fixed both: excluded `metric_type = 'daily_resting_heart_rate'`, and ran the shift in two phases via a large safe offset (-10000 days, then +10000 days -6 hours) to avoid any mid-statement collision. 5712 rows updated; spot-checked specific rows before/after, confirmed `daily_resting_heart_rate` and Wyze-sourced rows untouched.
- [x] 8. Re-checked the dashboard's biometric cards against the real data: a reading Google reported at `2026-08-19T04:11:00Z` (would have shown as 19 Aug) now correctly shows as `2026-08-18 22:11:00` local -- 18 Aug, the actual evening the user weighed in.
- [x] 9. Run `/changelogger` then `/commit` once verified.
