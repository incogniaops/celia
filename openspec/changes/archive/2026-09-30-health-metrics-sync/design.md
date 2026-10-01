# Design

## Context

Six Google Health API calls were already manually verified working during the hackathon (real requests via curl, documented in `docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md`, US-03): `weight`, `body-fat`, `heart-rate`, `daily-resting-heart-rate`, `steps`, `sleep`. That verification used a manually-obtained access token (OAuth 2.0 Playground) and the existing OAuth client credentials at `.secrets/client_secret_919644961981-....json` (client ID/secret only — no redirect URI for celia's own app is registered on it yet, only the Playground's). This change makes the running app able to get and refresh its own token, and turns those six verified calls into a real sync routine.

## Goals / Non-Goals

**Goals:**
- A real OAuth authorisation code flow hosted by celia itself, so no manual Playground step is needed again.
- Automatic access-token refresh using the stored refresh token.
- A sync routine covering all six confirmed data types, reusing what was learned about each one's quirks (kebab-case URL data-type IDs, per-type filter field names, steps/sleep needing pagination, point-sample types not).
- Resolve BR-06 (Google Health authoritative over MyTherapy for weight/steps) by giving the dashboard (a later capability) one normalised table to read both kinds of value from.

**Non-Goals:**
- The dashboard view itself (separate capability, `dashboard`) — this change only makes the data available in Postgres.
- Scheduled/automatic background sync (e.g. a cron job) — the product spec's US-03 says "a sync the user triggers or schedules," but scheduling infrastructure is out of scope here; `POST /sync/google-health` is user-triggered only for this MVP.
- Multi-user OAuth (per-user credentials) — one `GoogleHealthCredential` row, matching the single-user MVP.
- Interpreting sleep stage detail or generating insights — stored as-is in `raw_json` for a future dashboard to render.

## Decisions

**OAuth credentials via environment variables, not the mounted `.secrets/` file**: `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` env vars, matching how `DATABASE_URL` already works. *Alternative considered*: mount `.secrets/client_secret_*.json` into the container and parse it at startup. Rejected — one more file-shaped dependency to keep in sync across Podman/Docker/Kubernetes (Iteration 2) when two plain env vars do the same job and fit the pattern already established.

**Token storage: a `GoogleHealthCredential` Postgres row, not a file**: consistent with the single-user MVP already storing everything else in Postgres; a single row (`id=1` convention, like a settings table) holds `access_token`, `refresh_token`, `access_token_expires_at`, `last_synced_at`, `last_sync_status`, `last_sync_error`.

**`health_metrics` table shape**: one table for all six types, not six tables. *Alternative considered*: a table per metric type (mirroring `glucose_readings`/`medication_doses`, one table per capability's primary concept). Rejected here specifically — glucose and medication doses are each a single concept with a stable shape; these six types are variations on "one number at one time" (weight, body-fat %, heart rate, resting heart rate, step count) plus one richer shape (sleep stages), and BR-06's precedence rule needs a single place to look up "the weight/steps value for date X" regardless of which of the six types supplied it. Columns: `metric_type` (string: `weight`, `body_fat`, `heart_rate`, `daily_resting_heart_rate`, `steps`, `sleep`), `recorded_at` (timestamp — the sample time for point types, interval start for `steps`, sleep-session start for `sleep`, midnight UTC for `daily_resting_heart_rate`'s date-only value), `value` (numeric — grams-to-kg converted for weight, percentage for body fat, bpm for the two heart-rate types, count for steps, minutes-asleep for sleep's headline number), `unit`, `source_platform`/`source_package` (from `dataSource`, e.g. `com.hualai` = Wyze, `com.xiaomi.wearable` = Xiaomi), `raw_json` (the full original data point — necessary for sleep's stage breakdown, and as a safety net for anything the normalised columns don't capture, same pattern as `GlucoseReading.raw_row`).

**Deduplication: `ON CONFLICT DO NOTHING` on `(metric_type, recorded_at)`**, not upsert. *Rationale*: like glucose readings (and unlike MyTherapy doses), these are sensor/device readings from Google's own system of record — there is no "corrected later" scenario to accommodate, so glucose-ingestion's immutable-reading pattern applies, not medication-ingestion's upsert pattern.

**Per-type sync strategy, carried over from what was verified manually:**
- `weight`, `body-fat`, `heart-rate`, `daily-resting-heart-rate`: single `filter`-bounded request per sync (`{field}.sample_time.physical_time >= <last_synced_at or a 1-year bootstrap floor on first sync> AND < <now>`; `daily_resting_heart_rate` filters on `.date` instead). No pagination needed — confirmed working with a single request for weeks of history during manual testing.
- `steps`, `sleep`: paginate via `nextPageToken`, capped at a **30-day lookback window on first sync** (a deliberate bound, not tested manually at larger scale — steps returned only same-day intervals unpaginated in testing, implying many pages for a longer window; 30 days is a reasonable first-sync depth for a personal dashboard, revisit if it proves too shallow). Subsequent syncs use `last_synced_at` as the lower bound, which should be a small, fast page range.

**Redirect URI**: `http://localhost:8000/auth/google/callback` for local dev, added manually by the user to the existing OAuth client (the same one-time console step already done for `health_metrics_and_measurements.readonly` et al.). The homelab deployment's own redirect URI is a separate, later manual step (tracked as an open item below, not solved by this change).

## Risks / Trade-offs

- **Refresh-token revocation isn't self-healing**: if Google revokes the refresh token (e.g. after 6 months of inactivity, or a security event), sync fails until the user re-authorises manually. → Mitigation: the failure scenario above surfaces a clear message pointing at `/auth/google/login`; no attempt at automatic recovery.
- **Steps/sleep pagination depth is a guess (30 days)**: chosen without having tested pagination at scale end-to-end. → Mitigation: treat as adjustable; the sync's task 4 (end-to-end verification) will surface whether 30 days is a reasonable number of Google Health API calls.
- **`heart-rate` appears to be silently paginated by Google too, and this change doesn't paginate it**: confirmed live in task 4.2 — a 1-year `filter` window for `heart-rate` returned only 50 points in a ~49-second span (2026-09-27 18:49–18:50), not a year of history, even though the equivalent request for `weight`/`body-fat`/`daily-resting-heart-rate` correctly returned their full confirmed ranges. The point-sample sync (Decisions, above) assumed no pagination was needed for any of the four types based on manual testing that didn't specifically stress-test `heart-rate` at volume. → Accepted for this MVP (the other three point-sample types and both paginated types work correctly, and some heart-rate data beats none); paginating `heart-rate` like `steps`/`sleep` is a likely follow-up once the dashboard surfaces this gap visibly.
- **Running the test suite against the same Postgres instance as manually-uploaded real data caused real data loss**: `tests/conftest.py`'s `db_session` fixture `TRUNCATE`s its tables before every test; it defaulted to the same `DATABASE_URL` as the dev container, and a local pytest run during this change's own task 4.3 debugging wiped all four tables' real data (8,739 glucose readings, 466 medication doses, and the just-authorised Google credential). → Fixed: tests now default to a separate `celia_test` database, and `conftest.py` refuses to run at all if `DATABASE_URL` doesn't look like a test database. Real data had to be re-authorised (Google) and would need re-uploading (Libre/MyTherapy) to restore.
- **No background scheduling**: the user must remember to hit "sync" (Non-Goals). → Accepted for the MVP; a natural Iteration 2 addition once the dashboard exists to prompt for it.
- **`GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` in plain environment variables**: readable by anything with container/process access, same exposure level as `DATABASE_URL` already has. → Accepted, consistent with the project's existing security posture for this single-user homelab deployment.
