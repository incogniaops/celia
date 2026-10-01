# Changelog

## [2026-09-30] - Finalise MVP specification and adopt OpenSpec

- docs: reconcile biometric-cards-redesign's proposal.md and design.md
  with the three rounds of implementation that followed the initial
  plan — the "What Changes"/"Impact"/Goals sections still described
  only the first draft (BMI first, Muscle Mass included, both ages
  shown, GMI caption lines present), while the actual shipped behaviour
  had moved on through two further revisions; updated them to state the
  final card order and content directly, added the missing third
  revision's design rationale, and corrected the Time-in-range spec
  delta's wording to match the renamed "Glucose average" card
- feat: tidy up the biometric-card text — drop the "(not shown)" aside
  from the metabolic-age-delta card, rename "Glucose average / CV" to
  "Glucose average", and move the A1C card's mmol/mol figure onto its
  own small line below the percentage instead of inline beside it;
  remove the GMI/data-coverage caption lines from the A1C card entirely
- feat: revise the biometric-card row further — drop the Muscle Mass
  card (still ingested and stored, just no longer shown), move BMI to
  after Body Fat, and show only the metabolic-age-minus-chronological-age
  delta (e.g. "-3") instead of both ages side by side, so the dashboard
  never reveals the real age even indirectly — get_age_comparison now
  returns only the signed delta, never the real age itself, closing the
  same privacy gap PROFILE_BIRTH_DATE's move to an environment variable
  addressed in source control, now also addressed in the rendered page;
  verified end-to-end in a Podman container against real data — the
  real delta computes to exactly -3, matching the user's own expectation
- feat: redesign the dashboard's top biometric-card row — drop the Heart
  Rate and Daily Resting Heart Rate cards (still synced and stored,
  just no longer shown), add a BMI card computed independently from
  weight and height (rather than trusting the Wyze export's own stored
  BMI), and a metabolic-vs-chronological-age card using a birth date
  and the Wyze-sourced metabolic age; move the glucose average/%CV out
  of the "Time in range" text into its own card, next to A1C; height
  and birth date are read from new PROFILE_HEIGHT_M/PROFILE_BIRTH_DATE
  environment variables on Settings, not committed to source — an
  initial hardcoded-module attempt was caught and corrected before
  committing, since a real birth date and height would otherwise have
  been published in this repo's git history; verified end-to-end in a
  Podman container against real data (via the real, gitignored .env) —
  the independently-computed BMI (33.7) matches the Wyze-stored value
  exactly, and the card order and content match what was requested
- fix: defer both dashboard charts' construction to the next animation
  frame (plus an explicit resize() as a second safety net), after the
  user reported the glucose trend chart intermittently rendering at
  Chart.js's small default size instead of filling its container when
  switching between date-range presets — Chart.js measures its
  container synchronously at construction time, and can race the
  browser's layout pass for a just-swapped-in HTMX fragment; this is a
  browser-timing issue that can't be reproduced or proven fixed from an
  automated/headless check, so it applies the standard fix for this
  class of bug and awaits the user's own confirmation in their browser
- feat: replace the dashboard's manual "From"/"To" date pickers with four
  one-click range presets (last 7/14/30/90 days), computed client-side in
  local JS and fired via htmx.ajax(), no new dependency; the matching
  preset is pre-selected based on the currently-viewed range; fixed a real
  off-by-one found while wiring this up — the default range's start used
  a 30-day timedelta, which spans 31 calendar days inclusive, so it never
  matched the 30-day preset's true span; verified end-to-end in a Podman
  container against the exact URLs the client-side JS constructs for all
  four presets
- fix: store Google Health API timestamps in America/Mexico_City local
  time instead of UTC, and compute the dashboard's default date range's
  "today" from local time too — every other source (LibreView, MyTherapy,
  Wyze) already stored local time as-is, so Google Health was the one
  source showing readings under the wrong calendar day; backfilled the
  5,712 already-synced Google Health rows in the real dev database
  (excluding daily-resting-heart-rate, a plain date with no time-of-day,
  and Wyze-sourced rows, already correct), via a two-phase large-offset
  shift after a direct single-pass update hit a real unique-constraint
  collision between two `steps` rows; verified against real data showing
  the exact bug fixed (a reading at 2026-08-19T04:11:00Z, previously
  shown under 19 August, now correctly shown under 18 August)
- feat: add the mmol/mol (IFCC) equivalent and a "data spans X of Y days"
  coverage line to the dashboard's A1C card, matching LibreView's own
  "A1C calculada" report screen; verified end-to-end in a Podman container
  against the exact range from the user's own screenshot (3 July -
  30 September 2026) — the day-coverage figure matched exactly
  (61 of 90 days); the GMI itself was close but not identical over this
  wider window (6.3%/45 mmol/mol vs the screenshot's 6.0%/42 mmol/mol),
  consistent with the approximation already noted for glucose-pattern-views
- feat: add body-composition-ingestion — a stdlib-only (zipfile +
  ElementTree, no new dependency) parser for the Wyze scale's own
  "Body Composition Data" .xlsx export, since muscle mass and most other
  body-composition fields aren't available via the Google Health API;
  stores every measurement a row has (not just muscle mass), skipping
  fields the scale marked unread rather than as zero or null, ingests the
  export's optional "Heart Rate" section too, and only ever reads the
  first sheet (the logged-in account's own data), never a second profile
  sharing the same scale; add muscle mass and an estimated A1C (GMI) card
  to the dashboard's biometric profile; verified end-to-end in a Podman
  container against the real export (257 data points, re-upload produces
  zero duplicates, the other profile's data confirmed absent from the
  database)
- feat: add three glucose pattern views to the dashboard, inspired by the
  user's own LibreView AGP report — a time-in-range/GMI/%CV summary using
  the standard AGP consensus bands, an AGP percentile-band chart
  overlaying every day in the range onto one 24-hour axis, and a monthly
  glucose calendar (week rows, weekday columns) — all using Python's
  standard library only (no new dependency); verified end-to-end in a
  Podman container against the exact LibreView report period
  (17-30 September 2026), matching its GMI exactly (6.0%) and its
  time-in-range and per-day averages within 1-2 mg/dL
- feat: replace the dashboard's flat medication list with a
  medication-adherence calendar (one row per medication, one column per day
  in the selected range), inspired by MyTherapy's own monthly PDF report;
  same-day multi-dose medications are consolidated to a single status per
  day, with any rejected dose that day marking the whole day as not
  adhered; verified end-to-end in a Podman container against the real 466
  medication doses, including a genuine rejected stretch (Linagliptin,
  2026-09-09 to 2026-09-13)
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
