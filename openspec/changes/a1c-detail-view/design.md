# Design

## Context

The user's own LibreView "A1C calculada" screen shows 6.0% with "(42 mmol/mol)" beneath it and "Los datos abarcan 61 de 90 días" at the bottom -- confirming celia's existing GMI calculation (already verified exactly matching LibreView's 6.0% in `glucose-pattern-views`) and adding two details celia doesn't show yet.

## Decisions

**mmol/mol conversion**: `mmol/mol = 10.929 * (gmi_percent - 2.15)` -- the standard DCCT-to-IFCC conversion formula, the same one producing 42 mmol/mol from the report's own 6.0% (`10.929 * (6.0 - 2.15) = 42.08`, rounds to 42, matching the screenshot exactly).

**Data coverage**: `days_with_data` is the count of distinct calendar days (by `device_timestamp.date()`) with at least one glucose reading in the range; `days_in_range` is the inclusive day count of the selected range (`(end.date() - start.date()).days + 1`). Both computed in `get_glucose_summary_stats` from the same `get_glucose_trend` readings it already fetches -- no additional query.

**Where it lives**: both new figures are added to `glucose_summary` (not a separate dict), since they're part of the same "is there enough data to trust this number" story the GMI card already tells, and the function already returns `None` when there's no data at all (unchanged).

## Risks / Trade-offs

- None beyond what `glucose-pattern-views` already accepted for the GMI calculation itself -- this change only adds a unit conversion and a day-count, no new statistical assumptions.
