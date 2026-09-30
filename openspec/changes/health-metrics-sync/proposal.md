# Proposal

## Why

The third and last MVP data source is the only one already verified end-to-end manually (during the hackathon, via curl and the OAuth Playground — see US-03 and A-08 in the product spec): weight, body fat, heart rate, resting heart rate, steps and sleep, fed by a Wyze scale and a Xiaomi smartband through Health Connect and the Google Health API. glucose-ingestion and medication-ingestion are both done; this change is what lets the dashboard (not yet built) show all three sources together, and closes BR-06's precedence rule, which cannot mean anything until this capability's data actually exists.

## What Changes

- Add an OAuth flow inside the app itself (`GET /auth/google/login`, `GET /auth/google/callback`), since the manual OAuth Playground exchange used during the hackathon is not something the running app can repeat on its own: it needs to obtain and persist its own refresh token.
- Add a `GoogleHealthCredential` table (single row, single user) storing the access token, refresh token, its expiry, and the last sync's timestamp/status/error.
- Add a `health_metrics` table and a sync routine that calls the six confirmed Google Health endpoints (`weight`, `body-fat`, `heart-rate`, `daily-resting-heart-rate` via the `health_metrics_and_measurements.readonly` scope; `steps` via `activity_and_fitness.readonly`; `sleep` via `sleep.readonly`), refreshing the access token first when it has expired.
- Add `POST /sync/google-health` (the user-triggered sync celia's product spec calls for) and surface last-sync time/status on its response.
- Read the Google OAuth client ID/secret from environment variables (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`) rather than mounting the `.secrets/` JSON file into the container, consistent with how `DATABASE_URL` is already configured — add them to `.env.example` and `compose.yaml`.

## Capabilities

### New Capabilities
(none — this change implements an existing capability)

### Modified Capabilities
- `health-metrics-sync`: add requirements for the parts the existing spec assumes but doesn't define — how the OAuth token is obtained and kept fresh by the running app (not a one-off manual exchange), and the concrete `health_metrics` storage/dedup model. Both are needed to build this at all; neither was decided when the spec was written (during the hackathon, the token was obtained manually via the OAuth Playground, which is not a mechanism the deployed app can use).

## Impact

- **New code**: `app/auth/google.py` (OAuth login/callback/token-refresh), `app/health_metrics_sync.py` (the six-endpoint sync routine), a `GoogleHealthCredential` model + a `HealthMetric` model, a third Alembic migration, and a `sync` router.
- **New config**: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` environment variables (values come from the existing `.secrets/client_secret_*.json`, read once by the user, not by celia).
- **New manual step for the user, once**: add `http://localhost:8000/auth/google/callback` (and later, the homelab deployment's own address) as an authorized redirect URI on the existing Google Cloud OAuth client — the current one only has the OAuth Playground's redirect URI registered.
- **No impact** on glucose-ingestion or medication-ingestion. Resolves BR-06 (Google Health authoritative over MyTherapy for weight/steps) for the first time, since MyTherapy's weight/step rows exist but Google Health's haven't, until now.
