# Tasks

## 1. Data queries

- [x] 1.1 Add a query for the glucose trend (`record_type IN (0, 1)`, ordered by timestamp, within a date range) and verify a unit test against real-shaped fixture rows returns them in order, excluding other record types
- [x] 1.2 Add a query for insulin/carbohydrate markers (`record_type = 5`, or any row with a non-null insulin/carb field, within the same range) and verify a unit test confirms glucose-only rows are excluded
- [x] 1.3 Add a query for medication doses within the date range and verify a unit test returns the expected rows ordered by date
- [x] 1.4 Add the "current biometric profile" query (`DISTINCT ON (metric_type)`, most recent `weight`/`body_fat`/`heart_rate`/`daily_resting_heart_rate` regardless of the selected range) and verify a unit test confirms it returns one row per type and ignores `steps`/`sleep`
- [x] 1.5 Add the "has anything ever been ingested" check across all three tables and verify unit tests for both the all-empty and at-least-one-row cases

## 2. Dashboard route and template

- [x] 2.1 Add `GET /dashboard` accepting optional `start`/`end` query parameters (default: last 30 days, falling back silently on malformed input), wiring all four data queries together, and verify an integration test against seeded rows returns the expected data for a given range
- [x] 2.2 Add the Jinja2 template with a Chart.js (CDN) line chart for the glucose trend, an insulin/carbohydrate marker list, a medication list, and biometric-profile cards, and verify `GET /dashboard` renders without error against real seeded data
- [x] 2.3 Add the date-range form (HTMX-refreshed) and verify changing the range updates the rendered data via an integration test hitting `GET /dashboard?start=...&end=...`
- [x] 2.4 Add the empty-state view for when nothing has ever been ingested, and verify an integration test against an empty database renders it instead of the normal chart view
- [x] 2.5 Verify the rendered page's CSS keeps the chart within the viewport width at a mobile-sized viewport — confirmed by code inspection only (viewport meta tag, `canvas { width: 100% !important }`, `body { max-width: 900px }`, Chart.js `responsive`/`maintainAspectRatio: false`); no actual browser rendering was verified, since browser automation isn't available in this environment (Chrome extension blocked by corporate policy — see this project's earlier session history)

## 3. End-to-end verification

- [x] 3.1 Run the full flow in the local Podman container against the real data already loaded (8,739 glucose readings, 466 medication doses, 5,753 health metrics) and verify the dashboard renders the expected trend, markers, medication list and biometric profile for a real date range (7,605 glucose points; 466/466 medication doses; all 4 biometric cards with exact real values — weight 113.0kg/2026-09-30, body fat 34.4%/2026-09-27, heart rate 129bpm/2026-09-27, daily resting heart rate 86bpm/2026-07-18)
- [x] 3.2 Verify the empty state by pointing at a date range with no data and confirming the page still renders correctly (distinct from the all-time empty state, per design.md) — confirmed against the real container with a 2020 date range: "No insulin or carbohydrate entries" / "No medication doses in this range" shown, not the onboarding empty state
