# Design

## Context

Every ingestion path in celia except Google Health already stores local timestamps as-is: LibreView's CSV, MyTherapy's CSV and the Wyze `.xlsx` export all record the device/app's own local date-time strings, parsed directly with no timezone conversion (see `libre.py`, `mytherapy.py`, `wyze.py`). Google Health's API is the one source that returns true UTC instants (`Z`-suffixed ISO8601 strings), and `_parse_google_timestamp` (`app/health_metrics_sync.py`) currently just strips the `Z`/offset and stores the UTC wall-clock time as if it were local -- six hours off from America/Mexico_City (a fixed UTC-6 offset year-round; México abolished DST nationally in 2022, confirmed via `zoneinfo.ZoneInfo("America/Mexico_City")` returning `-06:00` for both a January and a July date).

The dashboard's default date range has the same class of bug: `_resolve_range` computes `today = datetime.utcnow()`, so opening the dashboard between 18:00 and 23:59 CST (already past midnight UTC) shows UTC's next calendar day as "today", shifting the default 30-day window's boundary by a day from the user's own perspective.

## Goals / Non-Goals

**Goals:**
- Make Google Health-sourced timestamps consistent with every other source: local America/Mexico_City time, no UTC conversion needed by the reader.
- Fix the dashboard's default-range "today" to reflect the user's own calendar day.
- Correct existing historical data to the new convention, not just new syncs going forward.

**Non-Goals:**
- Changing how Google's API is *queried*: the `since`/`until` filter bounds sent to Google remain true UTC instants (`_format_timestamp`'s `Z` suffix), since that's what the API's own filter syntax requires -- only the *stored* result of a returned data point changes.
- Changing `daily_resting_heart_rate`, which Google reports as a plain date (no time-of-day) -- there's nothing to convert.
- Changing OAuth token bookkeeping (`access_token_expires_at`, `last_synced_at`) or the PDF-fallback "now" timestamps in `libre.py`/`mytherapy.py` -- these are internal/rare-edge-case timestamps never shown to the user as a calendar day, unlike `recorded_at` and the dashboard's range boundary.

## Decisions

**A shared `app/timezone.py` constant** (`MEXICO_CITY = ZoneInfo("America/Mexico_City")`), rather than duplicating the string in both `health_metrics_sync.py` and `routers/dashboard.py` -- small, but avoids two independent sources of truth for which timezone celia runs on.

**`zoneinfo`, not a fixed `timedelta(hours=6)`.** Even though México's current policy is a fixed UTC-6 offset with no DST, `zoneinfo.ZoneInfo` is the correct primitive for "a place's local time" and costs nothing extra: confirmed working inside the actual Podman container image (`python:3.12-slim-bookworm` ships IANA tzdata), not assumed from macOS behaviour alone.

**Conversion point: at parse time, in `_parse_google_timestamp`**, not at display time in the dashboard. Every other source already stores local time as-is; converting at ingestion keeps `health_metrics.recorded_at` consistent with `glucose_readings.device_timestamp` and `medication_doses.actual_date` -- a reader never needs to know which table came from which timezone-aware source.

**One-time manual backfill, not an Alembic migration.** This is a one-off correction of already-synced real data to match a storage-convention fix, not a repeatable schema change every future deployment needs to replay -- an Alembic migration would permanently bake a "subtract 6 hours" step into migration history that makes no sense once the fix is in place and all new data is already correct. Scoped to `source_platform != 'wyze_export' AND metric_type != 'daily_resting_heart_rate'` -- the first scoping `SELECT` run against the real database caught that `daily_resting_heart_rate` rows (a plain date, never converted) were wrongly in scope, corrected before any write.

**Two-phase shift via a large safe offset, not a single `UPDATE ... SET recorded_at = recorded_at - interval '6 hours'`.** A direct single-statement shift hit a real unique-constraint collision: two `steps` rows six hours apart in their original timestamps landed on the same `(metric_type, recorded_at)` after one was shifted, while the other hadn't been processed yet in the same statement. Fixed by shifting the whole affected set by a large, collision-free offset first (`-10000 days`, far outside any other row's range), then by the exact remaining amount to land on the correct target (`+10000 days - 6 hours`) -- a uniform shift preserves relative uniqueness within the batch at every step, so neither phase can self-collide, and the large offset guarantees no collision against any row outside the batch either.

## Risks / Trade-offs

- **The backfill is a direct `UPDATE` against real production-like data**, the same category of operation that caused this project's earlier pytest data-loss incident. Mitigated by: scoping the `WHERE` clause precisely (verified against a real `GROUP BY` first), running it once interactively (not from an automated script), and spot-checking specific rows before/after.
- **A future Google Health API account outside México** would need this hardcoded timezone revisited -- out of scope for a single-user homelab project with one account.
