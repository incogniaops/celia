# Proposal

## Why

The user noticed celia uses GMT/UTC where it should use CST (America/Mexico_City). Two concrete places: (1) `health-metrics-sync` stores Google Health API timestamps as naive UTC rather than converting to local time first, so a reading's displayed date can be off by up to six hours' worth of calendar day; (2) the dashboard's default date range ("last 30 days") computes "today" from UTC, so late-evening CST sessions can already see UTC's next calendar day as "today". Every other data source (LibreView CSV, MyTherapy CSV, the Wyze export) already stores local timestamps as-is, with no UTC conversion -- Google Health is the only source out of step.

## What Changes

- Convert Google Health API timestamps to America/Mexico_City before storing `recorded_at`, for all six synced metric types that carry a time-of-day (not `daily_resting_heart_rate`, which Google already reports as a plain date).
- Compute the dashboard's default date range's "today" from America/Mexico_City, not UTC.
- One-time backfill of existing Google Health-sourced `health_metrics` rows (identified by `source_platform != 'wyze_export'`) by subtracting six hours, so historical data matches the new storage convention -- not a schema migration, a one-off data correction against the real database.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `health-metrics-sync`: synced timestamps are stored in America/Mexico_City local time, not UTC.
- `dashboard`: the default date range's "today" boundary is computed in America/Mexico_City, not UTC.

## Impact

- **Changed code**: `app/timezone.py` (new, shared `ZoneInfo("America/Mexico_City")` constant), `app/health_metrics_sync.py` (`_parse_google_timestamp`), `app/routers/dashboard.py` (`_resolve_range`).
- **No new dependency**: `zoneinfo` is standard library (Python 3.9+); confirmed working inside the actual Podman container image (Debian bookworm slim ships tzdata), not just on macOS.
- **One-time manual data correction**, not a schema change: `UPDATE health_metrics SET recorded_at = recorded_at - interval '6 hours' WHERE source_platform != 'wyze_export';` against the real dev database, run once during this change's rollout.
- **Google Health API querying itself is unaffected**: the `since`/`until` bounds sent to Google's API remain true UTC instants (required by the API's own `Z`-suffixed filter format) -- only how the *returned* data point's timestamp is stored changes.
