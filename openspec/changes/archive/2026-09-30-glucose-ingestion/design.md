# Design

## Context

Nothing has been scaffolded yet — this change writes the first application code in the repo, so it also establishes the FastAPI app skeleton that every later capability (medication-ingestion, health-metrics-sync, dashboard, data-sharing, sensor-log) will build on. A real sample export is already in hand at `data/abbott/RodrigoÁlvarez_glucose_30-9-2026.csv` (9,080 rows, confirmed record types 0/1/5/6 — see proposal.md and `docs/PS-CELIA-001-...md` for the full format analysis). Postgres is already running in the homelab; this change adds the first Alembic migration against it.

## Goals / Non-Goals

**Goals:**
- Stand up the minimal FastAPI app skeleton (`app/main.py`, `app/database.py`, `app/config.py`) that later capabilities reuse.
- Parse the confirmed LibreView CSV schema correctly, including the (timestamp, record type) dedup key from the spec delta.
- Provide a working upload form end-to-end: browser → FastAPI → Postgres.
- Containerise from the start (Containerfile + compose file), runnable under Podman locally, matching the project's OCI-compliance constraint.

**Non-Goals:**
- The dashboard view of ingested glucose data (separate capability, `dashboard`).
- Sensor-log correlation (separate capability, `sensor-log`) — this change stores readings only, it does not attempt to attribute them to a sensor.
- Authentication/authorisation — out of scope for the whole MVP (single user, BR-01 in the product spec covers this at the deployment level, not per-capability).
- A fully-featured LibreView PDF parser — the fallback only needs to extract the glucose summary, not match CSV granularity (see glucose-ingestion spec, requirement 2).

## Decisions

**App layout**: a single `app/` package — `main.py` (FastAPI app + router includes), `database.py` (SQLAlchemy engine/session, reads `DATABASE_URL` from env), `models.py` (SQLAlchemy models, starting with `GlucoseReading`), `routers/uploads.py` (this capability's routes), `templates/` (Jinja2), `parsers/libre.py` (CSV/PDF parsing, framework-independent — takes bytes, returns parsed rows, so it can be unit-tested without a running app or database).
*Alternative considered*: a single-file app. Rejected — later capabilities (medication-ingestion, health-metrics-sync) add their own routers and parsers; splitting from the start avoids a rewrite.

**CSV parsing**: use the standard-library `csv` module, not `pandas`. The format is simple (flat rows, one header line + one metadata line to skip) and the Container Image Construction Standard principle we're following (minimal images) argues against pulling in pandas for this.
*Alternative considered*: pandas — faster to write, but a much heavier dependency for a single-user app parsing a few thousand rows.

**Deduplication**: a unique constraint on `(device_timestamp, record_type)` at the database level (not just application-level checking), so a race or a retried upload can't create duplicates even under concurrent requests. `INSERT ... ON CONFLICT DO NOTHING` (Postgres upsert) implements the "keep first" rule from the spec delta in one statement per row, without a separate existence check.

**PDF fallback**: use `pypdf` for text extraction (pure Python, no system dependency like `poppler`/`pdftotext` — worth noting we hit exactly this gap testing MyTherapy's PDFs locally; avoiding a system package dependency keeps the container image simpler). Extract whatever summary text is present; do not attempt to reconstruct per-reading granularity from the PDF.

**File-type detection**: sniff by content, not filename or extension — check for the expected LibreView CSV header row vs. a PDF magic number (`%PDF`), and reject anything else per the glucose-ingestion spec's requirement 3. Relying on the upload's filename would be easy for the user to defeat by accident (e.g. renaming a MyTherapy file).

**Upload flow**: synchronous request/response (parse-and-insert within the HTTP request), not a background job. The files involved are small (the real sample is ~9,000 rows, well under a second to parse), and a single-user app has no concurrency pressure that would justify a job queue for this capability.

## Risks / Trade-offs

- **Malformed rows inside an otherwise-valid file**: the spec only covers whole-file rejection (requirement 3). Decision: skip individual unparseable rows and report a count to the user, rather than rejecting the whole file — a single corrupt row (e.g. from a manual CSV edit) should not lose an otherwise-good export. → Mitigation: surfaced to the user in the upload response, not silently swallowed.
- **PDF extraction fragility**: LibreView's PDF layout could change between app versions. → Mitigation: treat PDF ingestion as best-effort (per the spec's own "may be less granular than CSV" language); log what couldn't be parsed rather than failing the whole upload.
- **`ON CONFLICT DO NOTHING` silently drops disagreeing values**: per the spec delta's second scenario, this is intentional, but worth flagging as a real trade-off — if Abbott ever legitimately corrects a historic value, celia will never see the correction. Accepted for the MVP; revisit if it becomes a real problem.
