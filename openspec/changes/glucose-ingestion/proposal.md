# Proposal

## Why

celia has no working ingestion path yet — nothing has been scaffolded beyond the product spec and OpenSpec capability specs. FreeStyle Libre is the sole glucose source and the first data type on the dashboard's timeline, so it is the natural first capability to build: it unblocks the database schema, the upload-form pattern reused by medication-ingestion, and gives the project its first real data flowing end-to-end against the sample export already in hand (`data/abbott/`).

## What Changes

- Add a FastAPI upload endpoint and a Jinja2/HTMX upload form for a LibreView export (CSV or PDF).
- Add a parser for the confirmed LibreView CSV schema (`Dispositivo, Número de serie, Marca de hora del dispositivo, Tipo de registro, Historial de glucosa mg/dL, Escanear glucosa mg/dL, ...`), storing historic readings (record type 0), manual scans (type 1), and any insulin/carbohydrate entries present in the file.
- Add a minimal PDF-summary extraction path for a LibreView PDF report, as a lower-granularity fallback to the CSV.
- Add Postgres tables (via SQLAlchemy + Alembic) to store glucose readings, keyed by timestamp and reading type, independent of the CSV's "Número de serie" column (confirmed to be a device/app identifier, not the physical sensor serial — see glucose-ingestion spec, requirement 2).
- Reject files that do not match either expected format, with a clear reason shown to the user.

## Capabilities

### New Capabilities
(none — this change implements an existing capability, it does not introduce a new one)

### Modified Capabilities
- `glucose-ingestion`: add a requirement clarifying the deduplication strategy for overlapping re-uploads. The existing spec says overlapping periods must not produce duplicate readings, but does not say *how* celia decides a reading is a duplicate. LibreView CSV exports are cumulative (each export can contain the full device history, not just new data since the last export — confirmed against the real 9,080-row sample, which spans two months in one file), so the dedup key must be a stable per-reading identity, not a whole-file replace like medication-ingestion uses for MyTherapy's monthly files. Design below settles this as (timestamp, record type) uniqueness per ingested source.

## Impact

- **New code**: `app/` FastAPI package (first code in the repo — nothing exists yet), an `uploads` router, a `libre` parser module, SQLAlchemy models, an Alembic migration, and a Jinja2 upload-form template.
- **New dependencies**: `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `python-multipart` (required by FastAPI for file-upload form parsing), `jinja2`.
- **Database**: first Alembic migration, creating the glucose-readings table against the already-running Postgres instance.
- **No impact** on medication-ingestion, health-metrics-sync, dashboard, data-sharing or sensor-log — this change only touches glucose-ingestion, but establishes the FastAPI app skeleton (`app/main.py`, `app/database.py`) that those capabilities will share.
