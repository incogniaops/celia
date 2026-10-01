# Product Specification — Self-Hosted Diabetes Dashboard

| Field | Value |
|---|---|
| Product Specification ID | PS-CELIA-001 |
| Version | 1.2 |
| Status | **Engineering Ready** |
| Product Manager | Rodrigo Álvarez |
| Product Owner | Rodrigo Álvarez |
| Date | 2026-09-29 |
| Last Updated | 2026-09-30 |

**Version 1.2 note:** This revision brings the specification back in line with what was actually built during the hacking days, which grew beyond the original v1.1 MVP scope through ongoing user feedback: a fourth data source (US-07, Wyze body-composition export), a substantially richer dashboard (medication-adherence calendar, time-in-range/AGP/monthly-glucose-calendar pattern views, A1C/BMI/metabolic-age cards, date-range presets), and a corrected BR-06 (the real cross-source precedence is between Google Health and Wyze, not MyTherapy, which never persists competing data at all). US-05 (sharing) and US-06 (sensor log) remain as specified but not yet built.

## 1. Delivery Context

**Parent Use Case (Epic):** UC-01 — Personal Health Data Consolidation.
*Business objective:* one self-hosted place to bring together a single person's diabetes-related data — glucose readings, medication adherence and, eventually, other health metrics — so it can be reviewed and shared without depending on the separate, closed ecosystems (Abbott/LibreView, MyTherapy, Google/Apple) that produce it.

**Current Feature:** F1 — Self-Hosted Diabetes Dashboard.
The user (Rodrigo) ingests exports from FreeStyle Libre and MyTherapy, a Google Health API sync for weight, vitals (body fat, heart rate, resting heart rate) and activity (steps, sleep), and a Wyze body-composition export (muscle mass, BMI, body water, lean body mass, bone mass, protein, visceral fat, BMR, metabolic age, skeletal muscle rate, fat content, subcutaneous fat, plus its own weight/body-fat/heart-rate readings). He views all of it as one consolidated, time-aligned dashboard: a glucose trend with insulin/carbohydrate markers, a medication-adherence calendar, glucose pattern views (time-in-range, ambulatory glucose profile, monthly calendar), and a biometric-and-glucose-summary card row (metabolic-age delta, weight, body fat, BMI, glucose average, estimated A1C), filterable by one-click date-range presets (7/14/30/90 days) — in a browser on desktop or mobile. He can produce a read-only view he shares with his doctors.

**Current Product Iteration:** MVP (México Tech Hub SDD Hackathon, 2026-09-21 to 2026-10-02; core hacking days 2026-09-29 to 2026-10-01).

**MVP Statement:** The smallest valuable capability is a self-hosted dashboard that ingests FreeStyle Libre glucose exports and MyTherapy medication reports, plus weight, vitals and activity data via the Google Health API, and shows them together on one responsive, read-only-shareable screen. This replaces manually cross-referencing three separate apps/portals before a doctor's appointment.

**Known Future Product Specifications**

| Feature / Iteration | Status |
|---|---|
| F1 — Iteration 2 (multi-user: additional family members, doctor accounts with scoped access) | Planned, not yet specified |
| F1 — Iteration 2 (Apple Health integration) | Planned, not yet specified |
| F1 — Iteration 2 (automatic/scheduled ingestion instead of manual upload) | Planned, not yet specified |

Future Product Specifications beyond these are expected but have not yet been defined.

## 2. Overview

**Business Problem:** Diabetes management data is split across three closed systems (LibreView, MyTherapy, Google Health/Fit), none of which talk to each other, forcing the user to manually reconstruct the full picture before sharing it with a doctor.

**Product Summary:** A single self-hosted dashboard that ingests glucose data (FreeStyle Libre — the sole source of glucose readings), medication-adherence data (MyTherapy), weight/vitals/activity data (Google Health API, fed by the user's Wyze scale and Xiaomi smartband via Health Connect) and body-composition data (a direct export from the Wyze scale's own app, for the fields Google Health doesn't expose), aligns it by date and time, and displays it in one responsive web view that can be shared read-only with private and public-sector doctors.

**Expected Business Outcome:** The user can open one screen — on a computer or a phone — to see glucose trends together with medication adherence, and can share that view with a doctor in under a minute, without exporting from three different apps first.

**Business Value:** Faster, more complete preparation for medical appointments; ownership of personal health data outside vendor ecosystems; a foundation that can grow to support more data sources and, eventually, other people (Iteration 2).

## 3. Business Context

**Current Situation:** Glucose data lives in LibreView (Abbott) — the sole source of glucose in celia — exportable only as a manual CSV or PDF download. Medication-adherence data lives in MyTherapy, exportable only as a manual monthly PDF report. Weight (from a Wyze smart scale) and activity data (from a Xiaomi smartband) are written to Android's Health Connect and, as confirmed live during the hackathon, reachable through the Google Health API (the successor to the Fitbit Web API) once Health Connect is explicitly connected inside the Google Health app. The Wyze scale also measures a good deal of body-composition data (muscle mass, body water, bone mass, metabolic age and more) that Google Health does not expose at all — that only exists in the Wyze app's own exportable "Body Composition Data" file. None of these are combined anywhere today.

**Desired Future State:** The user uploads or syncs exports into celia, which stores and normalises them, and always shows one current, combined view.

**Business Process Context:** Periodically (at minimum before a doctor's appointment), the user downloads a LibreView CSV/PDF and a MyTherapy PDF report, uploads them to celia, and lets it refresh its Google Health API sync. He then opens the dashboard — on a computer or phone browser — and, if needed, generates a read-only view or export to share with a doctor.

**Primary Business Actors:**
- **User (Patient):** the sole account holder in the MVP; uploads exports, triggers or reviews API sync, views the dashboard, and shares it with doctors.

**Primary Stakeholders:** The user himself, and the doctors (private and public-sector) who receive the shared view but do not access celia directly in the MVP.

## 4. Business Value

**Business Objectives Supported:** Consolidate personal health data outside vendor lock-in; reduce appointment-prep effort; keep ownership and control over sharing.

**Expected Benefits:**
- One place to see glucose, meals, insulin and medication adherence together.
- A read-only view or export the user can hand to any doctor, public or private, without a paid third-party app.
- An architecture that can grow to more data sources and more users after the hackathon.

**Success Measures:** See Section 11.

## 5. Scope

**In Scope**
- Ingest a FreeStyle Libre export from LibreView: CSV (glucose history, historic readings, manual scans, insulin and carbohydrate entries already recorded in Libre) and/or the LibreView PDF report, uploaded by the user.
- Ingest a MyTherapy monthly PDF report (medication adherence), uploaded by the user.
- Ingest weight, body fat, heart rate, resting heart rate, steps and sleep from the Google Health API (fed by the user's Wyze scale and Xiaomi smartband via Health Connect), via an authenticated sync the user triggers or schedules.
- Ingest a Wyze "Body Composition Data" export (`.xlsx`, uploaded by the user): muscle mass, BMI, body water, lean body mass, bone mass, protein, visceral fat, BMR, metabolic age, skeletal muscle rate, fat content, subcutaneous fat, and the export's own weight/body-fat/heart-rate readings — none of the body-composition fields are available any other way, since Google Health does not expose them.
- Normalise and time-align all ingested data into one data model, keyed by date and time.
- A consolidated dashboard view: glucose trend with insulin/carbohydrate markers (from Libre), a medication-adherence calendar (from MyTherapy), glucose pattern views (time-in-range summary, ambulatory glucose profile, monthly glucose calendar), and a biometric-and-glucose-summary card row (metabolic-age delta, weight, body fat, BMI, glucose average/%CV, estimated A1C), viewable for a chosen date range via one-click presets (last 7/14/30/90 days).
- Compute BMI and an estimated A1C (Glucose Management Indicator) from ingested data rather than ingesting them directly, using two fixed personal facts (height, birth date) that no ingestion source provides; the dashboard shows only the signed difference between metabolic age and chronological age, never the chronological age itself, so it never reveals the user's real age even indirectly.
- Responsive web UI usable in a desktop browser and a mobile browser, without a dedicated native app.
- Generate a read-only shareable view (link and/or exportable report) of the dashboard for a chosen date range, for sharing with a doctor.
- Self-hosted deployment (single instance, single user) on the user's own homelab server, as a Docker deployment or a Kubernetes deployment.
- Maintain a manually-entered sensor log (serial, start date, end date, and a status code at start and at close) for the user's FreeStyle Libre sensors, as the one deliberate exception to "no manual data entry" (see Assumption A-06 and US-06).

**Data Categories Shared with Doctors**

The read-only view generated by US-05 may include the following personal health data, all of it sensitive:

- **Biometric profile:** weight, height, body fat percentage, muscle mass, BMI, heart rate, resting heart rate, and the metabolic-age-vs-chronological-age delta (the chronological age itself is deliberately never shown, even on this view).
- **Glucose data:** readings and trends from FreeStyle Libre (the sole glucose source), plus derived time-in-range, ambulatory glucose profile and estimated A1C (GMI) figures.
- **Medication data:** medication names, schedules and adherence from MyTherapy.

This data is normally private. The user knowingly includes it in celia and in what he shares, in order to give his doctors a fuller picture. Height and birth date are fixed personal facts kept in celia's deployment configuration (environment variables), not in source control or the database, since no ingestion source provides either. Q-05 governs how it must be protected in storage and in transit to a shared link.

**Out of Scope (this iteration)**
- Manual data entry of glucose, meals, insulin or medication — all data enters celia only through uploaded exports. The sensor log (US-06) is the sole exception to this rule.
- Apple Health integration (deferred to Iteration 2).
- Automatic/scheduled ingestion of LibreView and MyTherapy exports (both remain manual uploads in the MVP, since neither exposes a public API).
- Multi-user support: additional patients, or doctor accounts with their own login inside celia.
- Alerting or clinical decision support (e.g. hypo/hyper warnings).
- Mobile native app (a mobile *browser* view is in scope; an installable app is not).
- Data editing or correction inside celia once ingested.
- Long-term historical import beyond what LibreView/MyTherapy exports provide in a single download.

**Assumptions**
- **A-01:** The user is the only account; no authentication/authorisation model for multiple users is required in the MVP beyond protecting the self-hosted instance itself.
- **A-02:** LibreView and MyTherapy exports are downloaded manually by the user from their respective portals/apps and uploaded to celia; celia does not authenticate against Abbott or MyTherapy directly. MyTherapy's CSV export ("Archive.csv") is the preferred format — confirmed to cover full history, not just one month — with the monthly PDF report as a fallback if the CSV isn't available.
- **A-03:** The Google Health API is reachable with a personal Google account and OAuth credentials the user provisions himself, in Testing publishing status with the user added as a test user — confirmed during the hackathon to need no Google verification/review at this scale (verification is only required above 100 users or for a public launch). In practice, the data behind it comes from a Xiaomi smartband (steps, sleep, cardio points, energy, via "Mi Fitness") and a Wyze smart scale ("Wyze — Never Wonder", weight), both currently visible in the Google Fit consumer app; celia consumes it through the Google Health API rather than integrating with Xiaomi or Wyze directly. Glucose is never sourced from Google Health — FreeStyle Libre (US-01) is the sole glucose source.
- **A-08:** The Google Health API requires two separate one-time setup actions before it returns third-party data at all, both confirmed live during the hackathon: (1) linking the Google account at `fitbit.google.com/auth/signup`, and (2) within the Google Health app, connecting Health Connect under Connections → Partner apps. Step (1) alone only exposes natively-entered Fitbit data (e.g. a manual weigh-in); only after step (2) does the API return real Wyze/Xiaomi data (confirmed: `dataSource.platform: HEALTH_CONNECT`). Historical backfill after connecting is partial — this user's Wyze history goes back to 2026-07-09, but the API only returned records from 2026-08-19 onward (see US-03).
- **A-04:** Doctors consuming the shared view do not need their own celia account; the share mechanism is a link or exported file they open outside celia.
- **A-05:** Self-hosting infrastructure (server/NAS, as discussed separately) is available and reachable only from networks the user controls or exposes deliberately.
- **A-06:** Sensor lifetimes vary in practice — some sensors failed early and were replaced later than usual — so gaps in the glucose timeline are not a reliable signal of a sensor change on their own. The sensor log is therefore captured manually rather than inferred, as the only manual-entry exception in celia.
- **A-07:** The "Estado" (status) code shown per sensor on the FreeStyle LibreLink app's "Acerca de" (About) screen is not documented by Abbott. Its meaning is unknown; celia stores it as an opaque string for the user's own reference (e.g. to compare against Abbott support later), not as a decodable error or health status.
- **A-09:** Height and birth date are fixed personal facts, not ingested data — no source (LibreView, MyTherapy, Google Health, Wyze) provides either. They are read from environment variables at deploy time, the same mechanism as other secrets (Google OAuth credentials), and are deliberately kept out of source control: an initial implementation attempt hardcoded them directly in application code, and the user caught, before committing, that this would have published a real birth date and height to the project's public git history.

**Dependencies:** See Section 12.

**Constraints**
- Hacking-day window: 2026-09-29 to 2026-10-01, ~4 hours/day, which bounds MVP scope tightly.
- No public API for LibreView or MyTherapy ingestion; both are file-upload based in the MVP.
- Single user, single self-hosted instance.

## 6. Supporting Product Artefacts

| Artefact | Owner | Status |
|---|---|---|
| México Tech Hub SDD Hackathon brief | User | Available (informal, personal project) |
| Sample LibreView CSV/PDF export | User | **Closed — in hand** |
| Sample MyTherapy CSV/PDF export | User | **Closed — in hand (CSV + 3 monthly PDFs)** |
| Google Health API credentials + Health Connect connection | User | **Closed — verified working (all six data types) during the hackathon** |
| Sample Wyze body-composition export | User | **Closed — in hand, verified working** |
| UX designs | — | Not planned for MVP; UI built directly against these user stories |

## 7. Functional Behaviour

**Summary:** The user uploads a FreeStyle Libre export, a MyTherapy report and a Wyze body-composition export, and connects a Google Health API sync. celia normalises all four into one timeline, alongside the user's manually-maintained sensor log, and shows a consolidated, responsive dashboard the user can view on desktop or mobile and share read-only with a doctor.

BR-01 (self-hosted, single-user access only) and Q-04/Q-05 apply to all User Stories.

---

### US-01 — Ingest a FreeStyle Libre export
**As the** User, **I want** to upload my LibreView CSV or PDF export, **so that** my glucose, meal and insulin history is available in celia without retyping it.

**Business Outcome:** Glucose readings, and any meal/insulin entries already recorded in Libre, are stored in celia and available to the dashboard.

**Acceptance Criteria**
- **AC-01.1** **Given** a LibreView CSV export file, **when** the user uploads it, **then** celia parses the Device Timestamp and Record Type columns and stores each historic reading, manual scan, insulin entry and carbohydrate entry with its original timestamp.
- **AC-01.2** **Given** a LibreView CSV export, **when** celia parses its "Número de serie" column, **then** it is treated as a device/app-installation identifier, not the physical sensor's serial number — the two are confirmed to differ (the CSV value is a UUID; the physical sensor serial, as shown in the FreeStyle LibreLink app, is an alphanumeric code such as `3MH01ME1GZD`). This column is not used for sensor attribution or for the sensor log (US-06).
- **AC-01.3** **Given** a LibreView PDF report instead of a CSV, **when** the user uploads it, **then** celia extracts the glucose summary data it contains and stores it, noting that PDF ingestion may be less granular than CSV.
- **AC-01.4** **Given** an uploaded file that does not match the expected LibreView format, **when** celia processes it, **then** the upload is rejected and the user is told the file could not be recognised.
- **AC-01.5** **Given** a Libre export that overlaps a period already ingested, **when** the user uploads it, **then** celia does not create duplicate readings for the overlapping period.

**Business Rules:** BR-02, BR-04
**Quality Attributes:** Q-05

---

### US-02 — Ingest a MyTherapy export
**As the** User, **I want** to upload my MyTherapy data export, **so that** my medication adherence is visible alongside my glucose data.

**Business Outcome:** Medication-adherence data is stored in celia and available to the dashboard.

**Confirmed technical details (verified against a real export, 2026-09-30):** MyTherapy offers a full-history **CSV export** ("Archive.csv"), not just the monthly PDF report originally assumed — the CSV is the preferred format, since it is structured and does not need PDF text extraction. Confirmed schema: `actual_date, scheduled_date, type, name, value, unit, status, note`, where `type` is one of `drug`, `activity` or `measurement`:
- `drug` rows are medication doses: `name` is the medication (e.g. "Metformina tabletas"), `status` is `confirmed` or `rejected` (richer than the "taken/missed/skipped" originally assumed), and `note` sometimes gives a reason for a rejected dose (e.g. "Agotado", "Cambio de medicamento").
- `activity` and `measurement` rows (steps, walking minutes, weight, etc.) also appear in this export. **Corrected from v1.1:** these are recognised (so a malformed row elsewhere in the file is still caught) but deliberately **not stored at all** — not even as a lower-priority record — deferred to health-metrics-sync/body-composition-ingestion, which cover the same metrics from sources celia does persist (Google Health, Wyze). There is consequently no actual overlap between a stored MyTherapy value and a stored Google Health/Wyze value for the same date; see the corrected BR-06.

**Acceptance Criteria**
- **AC-02.1** **Given** a MyTherapy CSV export, **when** the user uploads it, **then** celia stores each `drug` row as a medication-adherence record (medication name, timestamp, confirmed/rejected, and the rejection reason if present).
- **AC-02.2** **Given** the same MyTherapy CSV export also contains `activity` and `measurement` rows, **when** celia ingests it, **then** those rows are recognised but not stored, since weight/step-count data is covered by health-metrics-sync (US-03) and body-composition-ingestion (US-07) instead.
- **AC-02.3** **Given** a MyTherapy monthly PDF report instead of the CSV, **when** the user uploads it, **then** celia extracts what medication-adherence data it can from the PDF, as a fallback when the CSV isn't available.
- **AC-02.4** **Given** an uploaded file that is not a recognisable MyTherapy CSV or PDF, **when** celia processes it, **then** the upload is rejected and the user is told the file could not be recognised.
- **AC-02.5** **Given** a MyTherapy export covering a period already ingested, **when** the user uploads it again, **then** the newer export replaces the previously stored data for the overlapping period rather than duplicating it.

**Business Rules:** BR-02, BR-04, BR-06
**Quality Attributes:** Q-05

---

### US-03 — Sync weight, vitals and activity data via the Google Health API
**As the** User, **I want** celia to pull my weight, body fat, heart rate, resting heart rate, steps and sleep (Wyze scale and Xiaomi smartband) from the Google Health API, **so that** they are visible alongside my glucose data without a manual export step. (Glucose is never part of this sync — FreeStyle Libre, US-01, is the sole glucose source.)

**Business Outcome:** Weight, body fat, heart rate, resting heart rate, steps and sleep data is stored in celia and available to the dashboard, refreshable on demand.

**Confirmed technical details (verified live during the hackathon, 2026-09-30):**
- OAuth scopes: `googlehealth.health_metrics_and_measurements.readonly` (weight, body fat, heart rate, daily resting heart rate), `googlehealth.activity_and_fitness.readonly` (steps), `googlehealth.sleep.readonly` (sleep) — all three added and verified working.
- Endpoint pattern: `GET https://health.googleapis.com/v4/users/me/dataTypes/{dataType}/dataPoints`, authenticated with `Authorization: Bearer {access_token}`. Data type IDs in the URL are kebab-case, not the camelCase used in field names — confirmed working values: `weight`, `body-fat`, `heart-rate`, `daily-resting-heart-rate`, `steps`, `sleep`.
- Query parameter `filter` (not `startTime`/`endTime`) using AIP-160 syntax. Interval-based types (`steps`, `sleep`) filter on `{type}.interval.start_time` (steps) or `{type}.interval.end_time` (sleep); sample-based types (`weight`, `body_fat`, `heart_rate`) filter on `{type}.sample_time.physical_time`; the daily-summary type (`daily_resting_heart_rate`) filters on `.date`.
- Response shape varies by type: `weight.weightGrams`, `bodyFat.percentage`, `heartRate.beatsPerMinute`, `dailyRestingHeartRate.beatsPerMinute` (keyed by `date`), `steps.count` (per time interval), `sleep.stages[]` + `sleep.summary` (minutes asleep/awake, stage breakdown: LIGHT/DEEP/etc.) — plus `dataSource.platform`/`recordingMethod`/`device`/`application` on all of them.
- **Pagination matters for steps and sleep:** default page size is much smaller for these (25 for sleep, per Google's docs; steps returned only the current day's intervals in one page during testing). A single unpaginated call will not retrieve full history — celia's sync must follow `nextPageToken` across pages to backfill properly, unlike weight/body-fat/heart-rate where a wide `filter` range was sufficient in testing.
- **Required setup, three steps, all confirmed necessary in practice:**
  1. Link the Google account at `fitbit.google.com/auth/signup`. On its own this only exposes data entered natively in Fitbit/Google Health (e.g. a manual weigh-in made during linking, `dataSource.platform: FITBIT`) — not Wyze/Xiaomi data.
  2. In the **Google Health app** (Android, formerly Fitbit) → **Connections** → **Partner apps / Apps and services** → connect **Health Connect**. This is the step that actually bridges Wyze/Xiaomi (which write to Health Connect) into Google Health.
  3. Only after step 2 does the API return real third-party data, tagged `dataSource.platform: HEALTH_CONNECT`, `recordingMethod: PASSIVELY_MEASURED`, with `dataSource.application.packageName` identifying the source app (`com.hualai` = Wyze, `com.xiaomi.wearable` = Xiaomi).
- **Known limitation — historical backfill varies by data type, confirmed live, not a fixed global cutoff:**
  - `weight`: 37 points from 2026-08-19 onward (Wyze's own history in Google Fit goes back to 2026-07-09 — not fully backfilled).
  - `body-fat`: 13 points from 2026-08-20 onward (Wyze).
  - `heart-rate`: only returns a very narrow recent window without an explicit filter (Xiaomi) — needs a wide `filter` range to pull more history; not yet confirmed how far back it actually goes.
  - `daily-resting-heart-rate`: 41 points, **2026-01-13 to 2026-07-18** — the deepest history of the four, and from a different period than the others.
  - `steps`: without pagination, only returned same-day intervals (fine granularity, ~15–30 min buckets) — full history requires paging through `nextPageToken`, not yet tested end-to-end.
  - `sleep`: 25 points (the default page size for this type), **2026-09-16 to 2026-09-30**, including full sleep-stage detail (LIGHT/DEEP) and summaries — deeper history also requires pagination.
  - Treat each data type's available range independently; do not assume one type's coverage implies another's.

**Acceptance Criteria**
- **AC-03.1** **Given** the three-step setup above is complete, **when** a sync is triggered, **then** celia retrieves new weight, body-fat, heart-rate, daily-resting-heart-rate, steps and sleep records since the last successful sync (or, on first sync, as far back as each type's API response returns, paginating via `nextPageToken` for steps and sleep) and stores them.
- **AC-03.2** **Given** a sync in progress, **when** it completes, **then** the user sees when the sync last ran and whether it succeeded.
- **AC-03.3** **Given** the Google Health API is unreachable, returns an error, or the account/Health Connect connection is incomplete (`ACCOUNT_NOT_LINKED` or similar), **when** a sync is attempted, **then** celia shows the sync failed with the reason, and existing data is left unchanged.
- **AC-03.4** **Given** overlapping records already retrieved in a previous sync, **when** a new sync runs, **then** celia does not create duplicate readings.
- **AC-03.5** **Given** a data type's known historical gap, **when** the user views the dashboard for a date earlier than that type's coverage, **then** the absence of data there is not shown as an error for that type — it is simply outside what the integration can provide, and does not affect other data types that may cover that date.

**Business Rules:** BR-02, BR-04, BR-06
**Quality Attributes:** Q-03, Q-05

---

### US-04 — View the consolidated dashboard
**As the** User, **I want** to see glucose, medication adherence, biometric and glucose-pattern data together on one screen, for a chosen date range, **so that** I can understand my own patterns and prepare for a doctor's appointment.

**Business Outcome:** The user has one combined, time-aligned view of all ingested data, on any device with a browser.

**Evolved beyond the original MVP scope, through ongoing user feedback during the hacking days:** the flat medication list became a medication-adherence calendar; three glucose pattern views were added (time-in-range summary, ambulatory glucose profile, monthly glucose calendar); the biometric profile gained computed BMI and a privacy-conscious metabolic-age delta, dropped muscle mass and heart rate/resting heart rate as shown cards (all three continue to be ingested, just not displayed), and gained an estimated A1C (GMI) card; and the manual date pickers were replaced with one-click range presets.

**Acceptance Criteria**
- **AC-04.1** **Given** ingested data from at least one source, **when** the user opens the dashboard, **then** glucose readings are shown as a trend line, with insulin/carbohydrate markers aligned to the same timeline, a medication-adherence calendar for the selected range, glucose pattern views, and a biometric-and-glucose-summary card row shown alongside it.
- **AC-04.2** **Given** the user selects one of the four date-range presets (last 7, 14, 30 or 90 days), **when** the dashboard refreshes, **then** only data within that range is shown, immediately, with no separate confirmation step; the preset matching the currently-viewed range, if any, is shown as selected.
- **AC-04.3** **Given** the dashboard is opened from a desktop browser or a mobile browser, **when** it renders, **then** the layout adapts to the screen size and remains usable without horizontal scrolling of the main chart, and charts reliably fill their container after a range-preset refresh rather than intermittently rendering at a fixed small size.
- **AC-04.4** **Given** no data has been ingested yet, **when** the user opens the dashboard, **then** an empty state explains how to upload a Libre export, upload a MyTherapy report, connect Google Health, or upload a Wyze body-composition export.
- **AC-04.5** **Given** a medication has more than one scheduled dose on the same day, **when** the calendar shows that day, **then** it shows one consolidated status per medication per day (any `rejected` dose that day marks the whole day as not adhered to), not a separate row per scheduled time.
- **AC-04.6** **Given** glucose readings exist in the selected range, **when** the dashboard renders, **then** it shows the percentage of readings in each of the five standard AGP bands, an ambulatory glucose profile (every day in the range overlaid onto one 24-hour axis as percentile bands, shown once at least two days of data exist), and a monthly calendar (week rows, weekday columns) with each day's average glucose.
- **AC-04.7** **Given** a current weight value and ingested metabolic-age data, **when** the biometric card row renders, **then** it shows, in order: a metabolic-age-vs-chronological-age delta (a single signed number, e.g. `-3` — never either age on its own, so the user's real age is never revealed even indirectly), weight, body fat, BMI (computed from weight and a fixed height, not read from the Wyze export's own stored BMI value), glucose average (with %CV shown alongside it), and an estimated A1C (GMI, shown as a percentage with the mmol/mol equivalent on its own line below it). Heart rate and resting heart rate are not shown as cards, even though both continue to be synced and stored.

**Business Rules:** BR-03, BR-06
**Quality Attributes:** Q-01, Q-06

---

### US-05 — Share a read-only view with a doctor
**As the** User, **I want** to generate a read-only view or export of my dashboard for a chosen date range, **so that** I can share it with a doctor without giving them access to celia itself.

**Business Outcome:** A doctor receives the relevant data for the chosen period without needing an account in celia.

**Acceptance Criteria**
- **AC-05.1** **Given** a date range the user selects, **when** they choose to share, **then** celia produces a read-only view (link) or export (file) covering only that range.
- **AC-05.2** **Given** a generated read-only link, **when** it is opened by anyone who has it, **then** it shows the dashboard for that date range only, with no ability to upload, sync, or edit data.
- **AC-05.3** **Given** a shared link, **when** the user chooses to revoke it, **then** it no longer grants access.

**Business Rules:** BR-01, BR-03
**Quality Attributes:** Q-05, Q-06

---

### US-06 — Maintain a sensor log
**As the** User, **I want** to manually record which FreeStyle Libre sensor (serial, start date, start status code and, once known, end date and end status code) I wore during a given period, **so that** my glucose history stays correctly attributed to a physical sensor, and I keep a reference for sensors that failed early, even though sensors don't all last the same number of days. (The status code's meaning is undocumented by Abbott — see A-07 — so it is stored for reference, not interpreted by celia.)

**Business Outcome:** A reliable, user-maintained record of sensor periods, including their status codes, exists alongside the automatically ingested glucose data, independent of how long any individual sensor actually lasted.

**Acceptance Criteria**
- **AC-06.1** **Given** a new sensor the user has started wearing, **when** they add a log entry with its serial, start date and the status code shown in the FreeStyle LibreLink app's "Acerca de" (About) screen at that time, **then** celia stores it as an open-ended period (no end date yet).
- **AC-06.2** **Given** an open sensor-log entry, **when** the user records that sensor's end date and the status code shown for it at that point (whether it lasted the typical 14–15 days or failed earlier), **then** the entry is closed for that period, with both its start and end status codes stored.
- **AC-06.3** **Given** two sensor-log entries, **when** their date ranges would overlap, **then** celia rejects the overlapping entry and tells the user which existing entry conflicts.
- **AC-06.4** **Given** one or more sensor-log entries, **when** the user views the dashboard (US-04), **then** the active sensor for any given date is shown alongside the glucose trend for that date, together with its status code(s).
- **AC-06.5** **Given** a period of the glucose timeline with no matching sensor-log entry, **when** the user views the dashboard, **then** that period is marked as having an unlogged sensor, without blocking the rest of the view.
- **AC-06.6** **Given** the status code is only available while the sensor is still listed in the app's "last 3 sensors", **when** the user closes a sensor-log entry after it has aged out of that list, **then** celia still allows the end date to be recorded, with the end status code left blank rather than blocking the update.

**Business Rules:** BR-05
**Quality Attributes:** Q-05

---

### US-07 — Ingest a Wyze body-composition export
**As the** User, **I want** to upload the Wyze scale's own "Body Composition Data" export, **so that** muscle mass and the other body-composition fields Google Health doesn't expose are visible alongside my other biometric data.

**Business Outcome:** Muscle mass, BMI, body water, lean body mass, bone mass, protein, visceral fat, BMR, metabolic age, skeletal muscle rate, fat content and subcutaneous fat — none of which the Google Health API returns — are stored in celia and available to the dashboard.

**Confirmed technical details (verified against a real export):** The Wyze app exports an `.xlsx` workbook with a "Body Composition Data" section (one row per weigh-in: `Number, Date and Time, Weight(lb), Weight(kg), BMI, Body Fat, Muscle Mass, Muscle Mass %, Body Water, Lean Body Mass, Bone Mass, Protein, Visceral Fat, BMR, Metabolic Age, Skeletal Muscle Rate %, Fat Content, Subcutaneous Fat`) and an optional "Heart Rate" section below it (present only on scale models with a handgrip sensor). A quick weigh-in (foot contact too brief for bioimpedance) reports weight/BMI only, with every other field marked `"- -"` rather than a zero or blank value. The workbook can contain more than one sheet if the scale is shared with another person; the logged-in account's own data is always the first sheet.

**Acceptance Criteria**
- **AC-07.1** **Given** a Wyze body-composition `.xlsx` export, **when** the user uploads it, **then** celia stores every measurement present in each row as its own data point, keyed by its original date and time.
- **AC-07.2** **Given** a quick-weigh row with bioimpedance fields marked `"- -"`, **when** celia ingests it, **then** it stores only weight and BMI for that timestamp, not a zero or null value for the missing fields.
- **AC-07.3** **Given** the export's optional "Heart Rate" section, **when** it is present, **then** celia stores each of its readings alongside heart-rate data from other sources; when it is absent, the rest of the export is still ingested normally.
- **AC-07.4** **Given** an export with more than one sheet, **when** the user uploads it, **then** celia only stores the first sheet's rows, never any other sheet's data.
- **AC-07.5** **Given** an uploaded file that does not match the expected Wyze export format, **when** celia processes it, **then** the upload is rejected and the user is told the file could not be recognised.
- **AC-07.6** **Given** a re-uploaded export overlapping a period already ingested, **when** celia processes it, **then** it does not create duplicate data points for the overlapping timestamps.

**Business Rules:** BR-02, BR-04, BR-06
**Quality Attributes:** Q-05

## 8. Cross-cutting Business Rules

| Rule ID | Business Rule |
|---|---|
| BR-01 | Only the user (the single authenticated account) can upload data, trigger syncs, or manage sharing. Read-only shared links are the only access doctors have. |
| BR-02 | Data already ingested for a given period is not duplicated when the same period is ingested again from the same source; the most recently uploaded file for an overlapping period wins. |
| BR-03 | All dashboard views and shared views are time-aligned by date and, where available, time of day, across all sources. |
| BR-04 | Files that do not match the expected format for their declared source (Libre, MyTherapy) are rejected with a reason, and no partial data is stored from them. |
| BR-05 | Sensor-log entries (US-06) are the only manually-entered data in celia. Their date ranges must not overlap for the same user. Each entry stores a start status code, and an end status code once available. |
| BR-06 | **Corrected from v1.1 — verified against the real database and code, 2026-09-30.** Weight, body fat and heart rate can each arrive from both the Google Health API (US-03) and a Wyze body-composition export (US-07) for the same date; neither source is authoritative over the other — the dashboard shows whichever reading has the more recent timestamp, since both represent real readings of the same physical measurement. MyTherapy's weight/activity data (US-02) is a separate case: it is never stored at all (see US-02's corrected AC-02.2), so it never actually competes with either source, even though the original v1.1 BR-06 assumed it would. |

## 9. Cross-cutting Quality Attributes

| ID | Category | Quality Attribute |
|---|---|---|
| Q-01 | Performance | The dashboard renders a selected date range of up to 90 days within 3 seconds on a typical broadband or mobile-data connection. |
| Q-02 | Reliability | A failed upload or sync never corrupts or removes previously stored data. |
| Q-03 | Reliability | A Google Health API sync failure, or a rejected/failed upload (Libre, MyTherapy), is surfaced to the user rather than silently ignored. |
| Q-04 | Availability | The self-hosted instance is expected to be available whenever the user's home infrastructure is online; no formal uptime target in the MVP (single user). |
| Q-05 | Security / Privacy | All ingested data — biometric profile (weight, body fat, muscle mass, BMI, heart rate, resting heart rate, metabolic age), glucose readings and medication data — is sensitive personal health data, normally private, and is stored only on infrastructure the user controls. Height and birth date (fixed personal facts, not ingested data) are kept in deployment environment variables, never in source control or the database; the dashboard shows only the metabolic-age-vs-chronological-age delta, never the chronological age itself. Read-only shared links reveal only dashboard data for their date range, nothing else. |
| Q-06 | Accessibility / Usability | The dashboard is usable on both a desktop browser and a mobile browser without a dedicated app; text and charts remain legible on a phone screen. |

## 10. Deferred Behaviour

**Deferred Functional Behaviour**
- F1, Iteration 2:
  - Apple Health integration.
  - Automatic/scheduled ingestion (instead of manual upload) for LibreView and MyTherapy, if either exposes an API in future.
  - Multi-user support: additional family members as patients, and doctor accounts with their own scoped login.
  - Alerting or clinical decision support.
  - Installable mobile app.
- Editing or correcting ingested data within celia.

**Deferred Business Rules:** Access control rules for multiple patients and doctor accounts.

**Deferred Quality Attributes:**
- Formal availability/uptime targets (relevant once shared with others beyond the user).
- WCAG-level accessibility conformance (Iteration 2, once used by more than one person).

**Deferred Behaviour Rationale:** Outside the 3-day hackathon MVP window, or dependent on API availability the user does not yet have confirmed (LibreView, MyTherapy).

**Progressive Definition Note:** Deferred Behaviour is intentional. This specification is complete for the agreed MVP, and building should not infer or add deferred behaviour.

## 11. Success Measures

| Measure | Target | Owner |
|---|---|---|
| Time from opening celia to sharing a read-only view with a doctor | Under 1 minute | User |
| Data sources consolidated in one dashboard | 4 (Libre, MyTherapy, Google Health, Wyze body-composition export) | User |
| Manual data entry required | 0 (ingestion only via upload or API) | User |

## 12. Dependencies

| Dependency | Description | Status |
|---|---|---|
| LibreView export access | User's own LibreView account, to download CSV/PDF | Assumed available |
| MyTherapy export access | User's own MyTherapy account, to download the monthly PDF report | Assumed available |
| Google Health API + Health Connect link | GCP project, OAuth credentials, `fitbit.google.com` account link, and Health Connect connected inside the Google Health app — feeds the user's Wyze scale and Xiaomi smartband data into the API | **Closed — verified working (weight, body fat, heart rate, resting heart rate, steps, sleep)** |
| Wyze app body-composition export | User's own Wyze app, to export the "Body Composition Data" `.xlsx` file | **Closed — in hand, verified working** |
| Self-hosting infrastructure | Homelab server to run celia, as a Docker deployment or a Kubernetes deployment | Available |

## 13. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| No public API for LibreView or MyTherapy | Ingestion stays manual-upload only, adding friction | Accepted for the MVP; revisit if either vendor publishes an API |
| Google Health API historical backfill is partial once Health Connect is connected, and varies by data type (confirmed live: weight/body-fat from 2026-08-19, daily-resting-heart-rate from 2026-01-13, heart-rate window not yet fully characterised) | The dashboard cannot show data for a type before its own available range, even though the source app (Wyze/Xiaomi) has more history | Accepted as a hard limit of the integration (AC-03.5); not something celia can work around |
| 3-day hacking window is tight for three ingestion paths plus a dashboard | Scope may need to shrink mid-hackathon | Prioritise Libre + dashboard + sharing first; MyTherapy and the Google Health sync can follow if time is short |
| Corporate-approved base container images (Core Engineering's Container Image Bakery) are only reachable from Elsevier's network | Cannot be used as the base image for a homelab-hosted personal project | Use official public Linux base images instead, applying the same principles (minimal, pinned version, non-root, scanned) as the corporate Container Image Construction Standard |
| The homelab VM's runtime (Podman or Docker, undecided) could behave slightly differently from Podman on the Mac, and a future move to Talos/containerd (Iteration 2) adds a third runtime | Local testing might not fully predict behaviour on other runtimes | Keep the container image strictly OCI-compliant and avoid Docker-, Podman- or containerd-specific build features, so the same image runs identically everywhere |
| Glucose-timeline gaps do not reliably indicate a sensor change: analysis of the user's own August–September 2026 export found 17 gaps over 20 minutes, but only 3 matched the expected ~14–15 day sensor lifespan and ~60 min warm-up pattern; sensors that failed early broke the pattern further | Automatically inferring the sensor log from gaps would misattribute glucose history to the wrong physical sensor | Capture the sensor log manually instead (US-06, A-06, BR-05), rather than inferring it from timeline gaps |

## 14. Open Decisions

| Decision | Owner | Status |
|---|---|---|
| OD-01 Final self-hosting target | User | **Closed — homelab server, deployed via Docker or Kubernetes (OD-01a below)** |
| OD-01a Docker vs. Kubernetes for the MVP deployment | User | **Closed — a single VM in the homelab, running Podman or Docker as the container runtime; Podman for local development and testing on the user's Mac** |
| OD-01b VM operating system: Fedora vs. Ubuntu | User | Open |
| OD-02 Exact share mechanism: signed link vs. exported PDF/HTML file | User | Open |
| OD-03 Whether MyTherapy can be cut from MVP if time runs short (Google Health/weight is now verified working) | User | **Closed — moot; MyTherapy ingestion was fully built, not cut** |

## 15. Traceability

| Artefact | Reference |
|---|---|
| Use Case (Epic) | UC-01 Personal Health Data Consolidation |
| Feature | F1 Self-Hosted Diabetes Dashboard |
| Current Iteration | MVP (Hackathon, single-user) |
| User Stories | US-01 – US-07 |
| Business Rules | BR-01 – BR-06 (BR-01 applies to all stories) |
| Quality Attributes | Q-01 – Q-06 (Q-04, Q-05 apply to all stories) |
| Supporting Artefacts | Sample LibreView export, MyTherapy export and Wyze body-composition export (all in hand); Google Health API access (verified working) |

## 16. Product Readiness Assessment

**Engineering Readiness (Definition of Ready, 2026-09-30):** ☒ **Engineering Ready.** Core scope, actors, sources and MVP stories are defined, and all four data sources have real data in hand and/or verified working: LibreView export (in hand), Google Health API (weight, body fat, heart rate, resting heart rate, steps, sleep — all verified working), MyTherapy (CSV export + monthly PDFs, in hand), and the Wyze body-composition export (in hand, verified working). All seven user stories (US-01 – US-07) are built and verified end-to-end against real data, except US-05 (sharing) and US-06 (sensor log), which remain specified but not yet built. OD-02 (share mechanism) remains open but does not block the remaining build.

| Outstanding Action | Owner | Status |
|---|---|---|
| Obtain a real LibreView CSV/PDF export | User | **Closed — in hand** |
| Obtain a real MyTherapy export | User | **Closed — in hand (CSV + 3 monthly PDFs)** |
| Google Health API access (weight, via Health Connect) | User | **Closed — verified working (all six data types)** |
| Obtain a real Wyze body-composition export | User | **Closed — in hand, verified working** |

## 17. Engineering Handoff Notes

- **Volumes:** single user, single instance. No concurrency concerns for the MVP.
- **Deployment target:** a single VM in the user's homelab (OD-01a), OS still to be decided between Fedora and Ubuntu (OD-01b), running the container with Podman or Docker. Local development and testing happen on the user's Mac using Podman rather than Docker Desktop, since Podman is daemonless, rootless and drop-in CLI-compatible with Docker; build and run against an OCI-compliant image so it behaves the same regardless of which runtime ends up hosting it.
- **Future Kubernetes path (Iteration 2):** if celia moves to Kubernetes, the target is Talos Linux with containerd, not Docker or Podman. Keep the container image runtime-agnostic (OCI-compliant, no Docker/Podman-specific build features) so it can run under containerd unchanged.
- **Base image:** Elsevier's Container Image Construction Standard (Architecture space, Approved) requires images to be built from Core Engineering's Container Image Bakery, hosted internally (`elsols-docker.jfrog.io`) and reachable only from Elsevier's network — not usable for this homelab-hosted personal project. Apply the standard's *principles* instead — minimal base image, pinned version tag or digest, vulnerability scanning, non-root entrypoint user, one application per container — using an official public Linux base image (e.g. an official Debian or Alpine variant matching the chosen runtime).
- **Known external systems:** LibreView (manual export only, no public API confirmed), MyTherapy (manual PDF/CSV export only, no public API confirmed), Google Health API (verified working live during the hackathon for all six confirmed data types — see US-03 for the exact endpoint, scope, and the two-step account/Health Connect linking it requires; historical backfill is partial, varies by data type), Wyze app (manual `.xlsx` export only, no public API confirmed — see US-07).
- Ingestion is upload- or sync-triggered only; there is no manual data-entry UI in scope.
- Responsive web UI is required (desktop and mobile browsers); no native app.
- All data is personal health data — treat storage and any shared link as sensitive by default (Q-05).
