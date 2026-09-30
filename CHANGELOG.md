# Changelog

## [2026-09-30] - Finalise MVP specification and adopt OpenSpec

- feat: implement dashboard — one GET /dashboard page showing the glucose
  trend (Chart.js via CDN), insulin/carbohydrate markers, medication
  adherence and the current biometric profile (weight, body fat, heart
  rate, resting heart rate) for a date range (default: last 30 days),
  HTMX-refreshed without a full page reload, with a distinct empty state
  for "nothing ingested yet" versus an ordinary empty range; verified
  end-to-end in a Podman container against all real data loaded so far
  (7,605 glucose points, all 466 medication doses, all 4 biometric cards
  with exact real values)
- fix: point the test suite at a dedicated celia_test database instead of
  the dev/container database, and refuse to run at all if DATABASE_URL
  doesn't look like a test database — a local pytest run had wiped all
  real data (glucose readings, medication doses, a just-authorised Google
  credential) via the db_session fixture's per-test TRUNCATE, because it
  defaulted to the same database the running container was using
- feat: implement health-metrics-sync — app-hosted Google OAuth
  authorisation and refresh (GoogleHealthCredential), and a sync routine
  for weight, body fat, heart rate, daily resting heart rate, steps and
  sleep, normalised into one health_metrics table with (metric_type,
  recorded_at) deduplication; fixed a real bug where a same-day re-sync
  produced an empty/invalid date filter for daily-resting-heart-rate,
  which Google rejected outright; verified end-to-end against the real
  linked Google account in a Podman container (37 weight, 13 body-fat, 41
  daily-resting-heart-rate, 5,559 steps and 53 sleep rows, matching the
  ranges confirmed manually during the hackathon)
- feat: implement medication-ingestion — MyTherapy CSV/PDF parser and
  upload endpoint storing medication doses in Postgres, upserting on
  (actual_date, type, name) so a re-uploaded export corrects a changed
  status instead of duplicating or ignoring it; deduplicates same-key
  rows within one upload first, after the real export's 3 same-second
  duplicate log entries hit Postgres's "cannot affect row a second time"
  restriction on ON CONFLICT DO UPDATE; verified end-to-end against the
  real ~470-row sample export (466 unique doses) in a Podman container
- feat: implement glucose-ingestion — FastAPI upload endpoint and LibreView
  CSV/PDF parser storing glucose readings in Postgres, with a
  (device_timestamp, record_type) deduplication key and batched inserts to
  stay under Postgres's 65535-parameter-per-query limit on large exports;
  verified end-to-end against the real ~9,000-row sample export in a
  Podman container
- chore: require the changelogger and commit skills within OpenSpec's apply and archive operations guidance, so no change is applied or archived without a CHANGELOG.md entry and a proper commit
- feat: confirm Google Health API integration for weight, body fat, heart rate, resting heart rate, steps and sleep, sourced from a Wyze scale and a Xiaomi smartband via Health Connect
- feat: confirm MyTherapy CSV export as the preferred medication-adherence source, with the monthly PDF report as fallback
- feat: add a manual sensor log (US-06) as the sole exception to "no manual data entry", to track FreeStyle Libre sensor periods whose lifespans vary in practice
- docs: mark docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md as Engineering Ready (v1.1) after validating all three MVP data sources against real data
- chore: adopt OpenSpec for spec-driven development; add six capability specs under openspec/specs/ derived from the product specification's user stories
- chore: protect data/ and .secrets/ via .gitignore before any real health data or credentials could be committed

## [2026-09-29] - Initialise repository and licensing

- chore: initialise git repository with an SSH remote and the laboral identity
- docs: add the MIT LICENSE and a README with the project description and acknowledgements
- docs: draft the initial product specification (PS-CELIA-001) for the self-hosted diabetes dashboard MVP
