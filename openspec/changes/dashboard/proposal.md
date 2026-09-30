# Proposal

## Why

All three MVP data sources (glucose-ingestion, medication-ingestion, health-metrics-sync) are implemented and hold real data (8,739 glucose readings, 466 medication doses, 5,753 health metrics). None of it is visible anywhere yet — every capability so far only has an upload form or a sync button. This is the capability that makes celia actually useful day to day: one screen showing it all together.

## What Changes

- Add `GET /dashboard`, showing a glucose trend line for a selected date range (default: last 30 days), with medication-adherence entries and the current biometric profile (weight, body fat, heart rate, resting heart rate) alongside it.
- Add a date-range form (HTMX-refreshed, matching the upload forms' pattern) so the user can change the window without a full page reload.
- Add an empty state when no data has been ingested from any source yet, pointing at the three upload/connect entry points.
- Add a responsive layout (desktop and mobile browsers) using Chart.js (CDN, matching the existing htmx.org CDN pattern — no JS build step) for the glucose trend line.

## Capabilities

### New Capabilities
(none — this change implements an existing capability)

### Modified Capabilities
- `dashboard`: add a requirement clarifying how BR-06 (Google Health authoritative over MyTherapy for weight/steps) actually applies given what's already built. medication-ingestion's Non-Goals (see that change) decided *not* to persist MyTherapy's `activity`/`measurement` rows (including weight) at all — they're discarded at parse time. So there is currently only one stored source for weight in the whole system (`health_metrics`), and no live conflict for the dashboard to resolve. This is worth stating explicitly rather than silently building precedence logic against data that was deliberately never stored, or silently skipping BR-06 without saying why.

## Impact

- **New code**: `app/dashboard_data.py` (queries glucose/medication/health-metrics for a date range, plus "most recent value per metric type" for the biometric profile), a `dashboard` router, and `app/templates/dashboard.html`.
- **New dependency**: none — Chart.js is loaded from a CDN in the template, the same way `htmx.org` already is; no new Python package.
- **No database changes**: this change only reads from tables glucose-ingestion, medication-ingestion and health-metrics-sync already created.
- **Explicitly deferred (Non-Goals, detailed in design.md)**: sensor-log correlation (that capability isn't built yet), steps/sleep in the biometric profile (the dashboard requirement names only weight/body-fat/heart-rate/resting-heart-rate), and data-sharing's read-only view (separate capability, US-05).
