# Tasks

## 1. Project scaffolding and containerisation

- [x] 1.1 Create the `app/` package skeleton (`main.py`, `database.py`, `config.py`) and verify `uvicorn app.main:app` starts and a health-check route returns 200
- [x] 1.2 Add `pyproject.toml` with `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `python-multipart`, `jinja2`, `pypdf`, and verify a clean install succeeds in a fresh virtual environment
- [x] 1.3 Add a `Containerfile` (minimal official Python base image, pinned version, non-root entrypoint user) and verify `podman build` succeeds
- [x] 1.4 Add a compose file for local dev (app service + Postgres connection config) and verify `podman compose up` starts the app and it can reach Postgres
- [x] 1.5 Add `.env.example` documenting `DATABASE_URL` and verify the app reads its config from the environment at startup

## 2. Database model and migration

- [x] 2.1 Define the `GlucoseReading` SQLAlchemy model (device timestamp, record type, historic/scan glucose, insulin/carbohydrate fields, unique constraint on `(device_timestamp, record_type)`) and verify a unit test asserts the constraint is present on the table
- [x] 2.2 Initialise Alembic and write the first migration creating the `glucose_readings` table, and verify `alembic upgrade head` succeeds against the homelab Postgres instance
- [x] 2.3 Add an insert helper using `INSERT ... ON CONFLICT DO NOTHING` and verify a unit test confirms inserting a duplicate `(device_timestamp, record_type)` does not raise and does not create a second row

## 3. LibreView CSV/PDF parser

- [x] 3.1 Implement CSV parsing for the confirmed LibreView schema (skip the metadata line; parse Device Timestamp, Record Type, and glucose/insulin/carbohydrate columns) and verify a unit test against a trimmed fixture derived from `data/abbott/` parses the expected row count and values
- [x] 3.2 Implement file-type sniffing (LibreView CSV header vs. `%PDF` magic number vs. unrecognised) and verify a unit test covers all three cases
- [x] 3.3 Implement the PDF fallback extraction using `pypdf` and verify a unit test against a trimmed sample PDF extracts the glucose summary text without raising
- [x] 3.4 Skip individually malformed rows within an otherwise-valid CSV, collecting a count and reason rather than rejecting the whole file, and verify a unit test with an injected bad row confirms the good rows still ingest and the bad-row count is reported

## 4. Upload route and form

- [x] 4.1 Add `POST /uploads/libre` accepting a multipart file upload, wiring the parser and insert helper together, and verify an integration test uploads the trimmed fixture and confirms the expected rows are queryable afterwards
- [x] 4.2 Add the Jinja2/HTMX upload form template and verify `GET /uploads/libre` renders a working file-upload form
- [x] 4.3 Implement rejection responses for unrecognised files (per glucose-ingestion requirement 3) and confirm re-uploading an overlapping export creates no duplicate rows (per the deduplication requirement added in this change), verified by two integration tests

## 5. End-to-end verification

- [x] 5.1 Run the full flow against the real sample export (`data/abbott/RodrigoÁlvarez_glucose_30-9-2026.csv`) in a local Podman container, and verify all valid rows are stored and that re-uploading the same file creates zero additional rows
