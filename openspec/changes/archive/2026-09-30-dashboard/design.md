# Design

## Context

The database already holds real data across the three tables the other capabilities built: `glucose_readings` (8,739 rows; `record_type` 0/1 are glucose readings, 5/6/99 are insulin/carb/PDF-summary markers — see glucose-ingestion's parser), `medication_doses` (466 rows), `health_metrics` (5,753 rows across six `metric_type` values). This change only reads from them — no schema changes.

## Goals / Non-Goals

**Goals:**
- One page, `GET /dashboard`, showing glucose trend + medication adherence + current biometric profile for a date range.
- A date-range control that doesn't reload the whole page (HTMX, matching the upload forms' pattern).
- Usable on both desktop and mobile browsers without horizontal scrolling of the main chart.
- A distinct empty state when literally nothing has been ingested yet, versus an ordinary "no rows in this range" result.

**Non-Goals:**
- Sensor-log correlation (which sensor was active for a given glucose period) — that capability (`sensor-log`) isn't built yet; the dashboard shows glucose without sensor attribution for now.
- Steps and sleep in the biometric profile — the dashboard requirement names only weight, body fat, heart rate and resting heart rate; steps/sleep exist in `health_metrics` but showing them is a later addition, not silently bundled in here.
- data-sharing's read-only view (US-05) — a separate capability; this change only builds the authenticated view.
- Editing, annotating, or correcting any data from the dashboard — read-only, matching every other capability's scope.
- Real BR-06 precedence logic — see the spec delta: there's currently only one stored biometric source, so there's nothing to arbitrate yet.

## Decisions

**Charting: Chart.js via CDN, not a Python charting library**: matches the existing `htmx.org` CDN pattern (no JS build step, no new Python dependency). Data for the selected range is serialised into the template with Jinja2's `|tojson` filter and read by a small inline `<script>` block that constructs one Chart.js line chart.
*Alternative considered*: a server-rendered SVG/plot (e.g. via a Python library). Rejected — adds a dependency for a single chart, and Chart.js is simpler to make responsive (it manages canvas resizing itself).

**Glucose trend query**: `record_type IN (0, 1)` only (historic auto-readings and manual scans — both are glucose values). Insulin/carbohydrate rows (`record_type = 5`) and the PDF-summary marker (`record_type = 99`, see glucose-ingestion's `PDF_SUMMARY_RECORD_TYPE`) are queried separately and shown as a list of markers under the chart, not as chart data points, since Chart.js's base line chart doesn't cleanly mix a continuous glucose series with sparse discrete events on the same axis without an extra plugin this change doesn't need.

**Biometric profile = most recent value per metric type, not "within the selected range"**: the requirement says "the *current* biometric profile ... shown alongside it" — a separate concept from the date-range-scoped glucose/medication data. Implemented as one query using `DISTINCT ON (metric_type) ... ORDER BY metric_type, recorded_at DESC`, independent of whatever date range is selected for the chart.

**Date range**: defaults to the last 30 days; accepted via `?start=YYYY-MM-DD&end=YYYY-MM-DD` query parameters. Malformed or missing values fall back to the default silently (not an error) — this is a convenience control, not an API contract worth rejecting bad input on.

**Empty state vs. "no rows in range"**: these are different states. The empty state (per the existing requirement) fires only when `glucose_readings`, `medication_doses` and `health_metrics` are *all* empty (a single lightweight `EXISTS`-style check against each, not a full row count) — meaning nothing has ever been ingested. A selected range simply having no rows (e.g. a future date range) renders the normal page with empty chart/lists, not the onboarding empty state.

**Responsive layout**: plain CSS flexbox, no framework. The chart canvas is styled `width: 100%` with a fixed height and Chart.js's `responsive: true` + `maintainAspectRatio: false` options, which together avoid horizontal overflow on a phone-sized viewport without extra JS.

## Risks / Trade-offs

- **No sensor attribution on the glucose trend yet**: a real limitation until `sensor-log` exists, explicitly out of scope here (Non-Goals) rather than faked.
- **`DISTINCT ON` is Postgres-specific syntax**: acceptable — the whole project already commits to Postgres (`ON CONFLICT` is used throughout the other capabilities too).
- **Chart.js via CDN means the dashboard needs internet access to render charts**: consistent with the upload forms already depending on `htmx.org`'s CDN; revisit if the homelab deployment ever needs to work fully offline.
