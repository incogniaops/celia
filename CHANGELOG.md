# Changelog

## [2026-10-01] - Implement data-sharing as a PDF export

- docs: bring README.md in line with all seven user stories now being
  built -- add the sensor-log section and the PDF export to "What's
  built", drop the stale "not yet built" callout, bump the referenced
  spec version to v1.4, and add a LaTeX/Tectonic badge
- docs: bring PS-CELIA-001 (v1.3 -> v1.4) in line with US-06 now being
  built -- the last of the seven user stories, so all of US-01 - US-07
  are built and verified end-to-end against real data; correct
  AC-06.4/AC-06.5 for the actual dashboard surface (a dedicated "Sensor
  log" section listing overlapping entries and an unlogged-day count,
  not a per-date marker woven into the glucose trend chart as originally
  specified)
- chore: archive the sensor-log OpenSpec change, syncing its ADDED
  "Sensor log overlap view" requirement into the main dashboard spec;
  `openspec validate --specs` passes with 0 failures across all seven
  capability specs
- feat: implement sensor-log (US-06), the last unbuilt user story and
  celia's one deliberate manual-data-entry exception -- a new
  sensor_log_entries table (serial, start/end dates, start/end status
  codes, the end fields independently nullable so a period can be closed
  with its end date even when the status code has aged out of the
  FreeStyle LibreLink app's "last 3 sensors" list); GET/POST /sensor-log
  (list + record a new open period) and POST /sensor-log/{id}/close,
  plain HTMX-posted forms matching the upload pages' style, not the
  HTMX-dashboard style; a new overlap check (Python-side, over the
  handful of existing rows) rejects a new entry whose range would overlap
  an existing one, naming the conflict, checked only on insert since
  closing an entry can only shrink its range, never introduce a new
  overlap -- and since two open-ended entries always overlap each other,
  this same check already guarantees at most one open entry can exist at
  a time, with no separate rule needed; a new "Sensor log" dashboard
  section lists entries overlapping the selected range and how many days
  in it remain unlogged, without blocking any other section when the log
  is empty; verified end-to-end in the Podman container (create, close,
  overlap rejection, dashboard integration) against the real dev database
- chore: remove the old openspec/changes/data-sharing-pdf-export/ files --
  the previous archive commit added their copy under
  openspec/changes/archive/ but missed staging this deletion
- chore: archive the data-sharing-pdf-export OpenSpec change, syncing its
  rewritten "Generate a scoped read-only share" requirement (PDF mechanism,
  all six scenarios) into the main data-sharing spec, and removing the two
  link-specific requirements ("Read-only access for share recipients",
  "Revocable shares") it superseded; `openspec validate --specs` passes
  with 0 failures across all seven capability specs
- feat: implement data-sharing (US-05) as a downloadable PDF export instead
  of a signed share link, resolving OD-02 -- a new GET
  /dashboard/export.pdf route (reusing the dashboard's own start/end
  range-resolution) renders a Jinja2 .tex template and compiles it with
  Tectonic, a single self-contained LaTeX engine binary added to the
  Containerfile rather than a full TeX Live install; its package cache is
  warmed at image-build time by compiling the real template (not a
  separately hand-maintained throwaway document) against synthetic sample
  data, so generating a report at runtime needs no network access
  (verified with podman run --network none); a new get_daily_glucose_profiles
  in dashboard_data.py reuses get_glucose_trend's readings grouped by
  calendar day for the report's daily-profile grid; the user's own name is
  read from a new PROFILE_NAME environment variable, following
  PROFILE_HEIGHT_M/PROFILE_BIRTH_DATE's existing precedent; a small square
  download-icon button sits next to the dark/light theme toggle
- fix: Jinja2's default doubled-paren-friendly delimiters broke on the
  template's own pgfplots coordinate lists (a literal "(" before a "((x))"
  variable confused Jinja2's own paren-balancing expression parser) --
  switched to the word-prefixed brace delimiters \BLOCK{ }/\VAR{ }, caught
  locally before it ever reached the Containerfile
- fix: an unescaped "%" in a band-target string (e.g. "<25%") silently
  truncated a LaTeX table row as a comment, merging it with the next row
  and breaking the table -- applied the existing latex_escape filter to it
- fix: the report's PDF compiled fine locally but failed offline at
  runtime with "File size11.clo not found", because the first hand-written
  cache-warming document used a different \documentclass font-size option
  than the real template; switched cache-warming to compile the real
  template (via a new warmup.py rendering it with synthetic data) so this
  class of drift is no longer possible, catching a second instance of the
  same drift (a missing pgfplots groupplots library) immediately
- fix: the daily-profile grid forced a page break every 4 week-rows
  regardless of how much room was left on the page -- the user flagged a
  30-day report as "horrendo" (cut short on page 1, page 2 almost entirely
  blank); removed the forced break and let LaTeX paginate each
  self-contained week-row naturally, so a 30-day range now renders on a
  single page
- fix: the user rejected the report's look twice more after the
  pagination fix -- the default serif font ("la fuente es horrenda") and
  bare floating text with no resemblance to the real Abbott/LibreView
  report it's modelled on ("el layout no se parece en absoluto"); switched
  to Latin Modern Sans via fontspec, loaded by its exact bundled .otf
  filename rather than by font name (this sandboxed build has no
  fontconfig database for the usual by-name lookup -- \setmainfont{Latin
  Modern Sans} failed outright, and an earlier helvet-based attempt
  compiled without error but silently stayed serif), and restructured
  every section into Abbott-style shaded tcolorbox panels with the top two
  made equal-height via tcbraster
- docs: bring PS-CELIA-001 (v1.2 -> v1.3) in line with US-05 now being
  built -- rewrite its acceptance criteria for the actual PDF-export
  mechanism, close OD-02, and correct BR-01/Q-05/A-04 and the readiness
  section, which all still described a signed share link

## [2026-09-30] - Finalise MVP specification and adopt OpenSpec

- docs: bring README.md in line with the current build and the anchor
  spec (PS-CELIA-001 v1.2) instead of the original pre-build MVP
  scope/status text — add a "What's built" section listing all four
  ingested sources and the full dashboard feature set actually shipped
  (time-in-range/AGP/monthly-calendar views, medication-adherence
  calendar, biometric cards, date-range presets, dark/light theme
  toggle), name US-05 (sharing) and US-06 (sensor log) as specified but
  not yet built, link openspec/specs/ alongside the anchor doc, and
  add licence/Python/FastAPI/SQLAlchemy/PostgreSQL/HTMX/Chart.js/
  Podman badges
- chore: archive the dark-light-theme-toggle OpenSpec change, syncing
  its "Dark/light theme toggle" requirement (and the two legibility
  scenarios added after the user's browser screenshot) into the main
  dashboard spec; `openspec validate --specs` passes with 0 failures
  across all seven capability specs
- fix: fix dark-mode legibility in the two Chart.js charts (glucose
  trend, AGP) and the hardcoded-colour "Time in range"/"Monthly glucose
  calendar" cells, found via the user's own browser screenshot right
  after the theme-toggle feature below was first deployed to the
  Podman container — Chart.js doesn't read Pico's data-theme and was
  rendering tick/legend/gridline text in its default light-page colour
  against the new dark background, and the pastel table/calendar
  cells' text was inheriting the dark theme's light default instead of
  staying readable against their own fixed backgrounds; both charts
  now read data-theme at build time and redraw via a new
  celia-theme-change event when the user toggles, and the pastel cells
  pin a fixed dark text colour matching their own background; the
  theme-toggle commit itself had first been committed, then reverted,
  because this environment has no browser automation and the user
  correctly pointed out that is exactly why the commit should have
  waited for their own browser confirmation rather than disclosing the
  gap after the fact — both the toggle and this legibility fix are
  committed together now that the user has confirmed them in their own
  browser
- feat: add a dark/light theme toggle to the dashboard, defaulting to
  dark when no preference is stored; the choice persists across
  reloads via localStorage, and the theme is set before first paint to
  avoid a flash of the wrong theme; scoped to the two Pico.css-styled
  pages (dashboard.html, dashboard_empty.html) — the three upload pages
  don't load Pico.css and have no visual theme to toggle; verified
  server-side in a Podman container that the script/button render
  once and are absent from the HTMX fragment response, so range-preset
  clicks don't reset or duplicate them; the flash-free rendering and
  click-to-toggle behaviour itself are real-browser-only concerns this
  environment has no browser automation for, same limitation as
  chart-resize-after-swap
- docs: bring PS-CELIA-001 (v1.1 -> v1.2) back in line with what was
  actually built, so it can be the anchor spec again — add US-07
  (Wyze body-composition export, the fourth data source, missing
  entirely from v1.1), rewrite US-04's acceptance criteria for the
  dashboard's full current feature set (medication-adherence calendar,
  time-in-range/AGP/monthly-glucose-calendar views, BMI/metabolic-age/
  A1C cards, heart-rate cards dropped, date-range presets), correct
  AC-02.2 and BR-06 (MyTherapy's activity/measurement rows are
  recognised but never stored at all — v1.1 wrongly assumed they
  competed with Google Health under a precedence rule; the real
  precedence is Google Health vs Wyze, most-recent-wins), add A-09
  (height/birth date as fixed environment-variable facts, not source
  control), and update Q-05, Section 11, Section 12 and the
  readiness/traceability sections to match
- docs: resolve the biometric-profile source-precedence inconsistency
  flagged during the archive pass — confirmed against real data that
  MyTherapy still never persists weight/activity (medication-ingestion's
  NON_PERSISTED_TYPES is unchanged), but Wyze genuinely does store
  weight/body-fat/heart-rate rows alongside Google Health (37/13/1 Wyze
  rows vs 36+1/13/50 Google Health rows for those three metric types),
  and get_current_biometric_profile has no precedence logic at all —
  just most-recent-`recorded_at`-wins, regardless of source; rewrote
  the dashboard's "Biometric profile source precedence" requirement to
  state that as the actual rule, instead of the stale "health_metrics
  (Google Health) only" claim
- chore: archive all 12 completed OpenSpec changes (glucose-ingestion
  through biometric-cards-redesign), syncing every delta into the main
  specs under openspec/specs/ in dependency order, with an
  agent-driven merge for each (not a blind copy) since most deltas
  modified or added to specs that had evolved since they were written;
  added a new body-composition-ingestion main spec (with a proper
  Purpose, not left as the TBD placeholder its delta omitted); all
  seven capability specs pass `openspec validate --specs` with no
  failures; known pre-existing inconsistency surfaced, not resolved
  here: dashboard's "Biometric profile source precedence" requirement
  still claims `health_metrics` is the only stored weight source, which
  body-composition-ingestion and health-metrics-sync's own
  MyTherapy-precedence requirement both now contradict — needs a real
  design decision, not a sync fix
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
