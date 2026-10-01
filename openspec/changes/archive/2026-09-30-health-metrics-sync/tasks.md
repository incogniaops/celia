# Tasks

## 1. Config, credentials model and migration

- [x] 1.1 Add `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` to `app/config.py`, `.env.example` and `compose.yaml`, and verify the app fails fast with a clear error at startup if they are unset (mirroring `DATABASE_URL`'s existing behaviour)
- [x] 1.2 Define the `GoogleHealthCredential` model (single-row: `access_token`, `refresh_token`, `access_token_expires_at`, `last_synced_at`, `last_sync_status`, `last_sync_error`) and the `HealthMetric` model (`metric_type`, `recorded_at`, `value`, `unit`, `source_platform`, `source_package`, `raw_json`, unique constraint on `(metric_type, recorded_at)`), and verify unit tests assert both tables' shapes and the constraint
- [x] 1.3 Write the third Alembic migration creating both tables, and verify `alembic upgrade head` succeeds against the running Postgres instance

## 2. OAuth login, callback and token refresh

- [x] 2.1 Add `GET /auth/google/login` redirecting to Google's OAuth consent screen with the confirmed scopes (`health_metrics_and_measurements.readonly`, `activity_and_fitness.readonly`, `sleep.readonly`) and `access_type=offline` (required to receive a refresh token), and verify a test asserts the redirect URL contains the expected client ID and scopes
- [x] 2.2 Add `GET /auth/google/callback` exchanging the returned code for tokens and upserting the single `GoogleHealthCredential` row, and verify an integration test (mocking the token endpoint) stores the access token, refresh token and expiry
- [x] 2.3 Add a token-refresh helper that exchanges the stored refresh token for a new access token when the stored one has expired, and verify a unit test (mocking the token endpoint) confirms it is called only when expired, not on every sync
- [x] 2.4 Handle a rejected refresh token by marking the sync failed with a message pointing at `/auth/google/login`, storing no partial data, and verify a unit test confirms this failure path leaves existing `health_metrics` rows unchanged (verified at the token-refresh layer here; the end-to-end DB-unchanged guarantee is covered by the sync routine's own failure test in group 3)

## 3. Sync routine for the six confirmed data types

- [x] 3.1 Implement the point-sample sync (`weight`, `body-fat`, `heart-rate`, `daily-resting-heart-rate`) using a single `filter`-bounded request per type, normalising each into a `HealthMetric` row (weight converted from grams to kg), and verify unit tests (mocking the Google Health API) cover all four types' response shapes, including `daily-resting-heart-rate`'s date-keyed (not `sampleTime`-keyed) response
- [x] 3.2 Implement the paginated sync (`steps`, `sleep`) following `nextPageToken`, bounded to a 30-day lookback on first sync and `last_synced_at` onward otherwise, and verify a unit test (mocking a two-page response) confirms both pages are retrieved and stored
- [x] 3.3 Insert all six types' normalised rows via `ON CONFLICT (metric_type, recorded_at) DO NOTHING`, and verify a unit test confirms re-running the sync over an overlapping window creates no duplicate rows
- [x] 3.4 Add `POST /sync/google-health` wiring token refresh and all six type-syncs together, updating `last_synced_at`/`last_sync_status`/`last_sync_error` on the credential row, and verify an integration test (mocking the Google Health API) triggers a sync and confirms the expected `health_metrics` rows exist afterwards
- [x] 3.5 Surface an unreachable/erroring Google Health API as a failed sync with the reason, leaving existing data unchanged, and verify an integration test asserts this for a simulated API error

## 4. End-to-end verification

- [x] 4.1 Add `http://localhost:8000/auth/google/callback` (and `https://celia.faraday.org/auth/google/callback` for the homelab) as authorised redirect URIs on the existing Google Cloud OAuth client (manual one-time step, done by the user)
- [x] 4.2 Run the full flow in the local Podman container against the real Google account already linked (`fitbit.google.com` + Health Connect, both already done during the hackathon): authorise via `/auth/google/login`, trigger `/sync/google-health`, and verify real weight/body-fat/heart-rate/daily-resting-heart-rate/steps/sleep rows land in `health_metrics`, matching the ranges and counts already confirmed manually in `docs/PS-CELIA-001-...md` (weight 37 rows from 2026-08-19, body-fat 13 from 2026-08-20, daily-resting-heart-rate 41 from 2026-01-13 to 2026-07-18 — all exact matches; steps 5,559 and sleep 53 rows for the 30-day bootstrap window; heart-rate only 50 rows in a narrow window — see design.md's updated Risks for why)
- [x] 4.3 Trigger a second sync immediately after and verify it creates zero additional rows for data already retrieved (also caught and fixed a real bug here: `daily_resting_heart_rate`'s date-only filter produced an empty/invalid range when `since` and `until` fell on the same calendar day, which Google rejected outright — see the spec's fix in `_build_filter`)
