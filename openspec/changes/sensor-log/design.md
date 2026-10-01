# Design

## Context

See proposal.md for motivation; see `openspec/specs/sensor-log/spec.md` for the full behaviour contract this change builds (already written, unchanged by this delta).

This codebase's existing per-capability pattern: a SQLAlchemy model in `app/models.py`, an Alembic migration (`alembic/versions/`), insert/query helpers in `app/repository.py`, a FastAPI router under `app/routers/`, and -- for upload-style capabilities -- plain HTML templates with no JS framework (`app/templates/upload_*.html`), distinct from the HTMX-driven dashboard templates. `app/dashboard_data.py` holds every dashboard-facing query function; `app/routers/dashboard.py`'s `_dashboard_context` assembles them into one template context.

## Goals / Non-Goals

**Goals:**
- Record and close sensor periods through a plain HTML form, matching the upload pages' style (this is manual data entry, celia's one deliberate exception -- it should look and feel like the same kind of page, not like the HTMX dashboard).
- Reject an overlapping entry at creation time, naming the conflict, per the spec.
- Surface sensor-log coverage (and gaps) for the dashboard's currently-selected range without blocking any other dashboard section if the sensor log is empty or incomplete.

**Non-Goals:**
- Enforcing serial uniqueness. The spec's actual invariant is non-overlapping *date ranges*, not unique serials (a user could, in principle, log the same physical sensor's serial twice across non-contiguous periods); inventing a uniqueness rule the spec doesn't ask for would be over-specifying.
- Editing or deleting an existing entry's start fields once recorded, or editing a closed entry. The spec defines exactly two actions -- record a new open period, close an open one -- and no others.
- Decoding or validating the "Estado" status code's format. It is stored as an opaque string (spec's "Status codes are opaque" requirement) -- not even validated as non-empty beyond what "required at creation, optional at close" already implies.
- A dedicated "at most one open entry" rule. See Decisions below -- this falls out of the overlap constraint for free.

## Decisions

**`sensor_log_entries` table: `serial`, `start_date`, `start_status_code` (all required), `end_date`, `end_status_code` (both nullable).** Dates are `Date`, not `DateTime` -- a sensor period is day-granularity (matching the FreeStyle LibreLink app's own "Acerca de" screen, which shows dates, not times). `end_status_code` stays nullable independently of `end_date` because the spec's own scenario allows closing a period with the end date recorded but the status code left blank (the sensor aged out of the app's "last 3 sensors" list by the time the user closes the entry).

**Overlap is checked only at creation, never at close.** Closing an entry only ever *shrinks* its range (from open-ended to a fixed end date), which cannot introduce a new overlap with anything that was already valid. Checking overlap again on close would be redundant work enforcing something structurally already guaranteed.

**An open entry is treated as covering `[start_date, +∞)` for overlap purposes.** Two entries overlap when `new.start_date <= (existing.end_date or +∞)` and `existing.start_date <= (new.end_date or +∞)`. Because two open entries always satisfy this (both extend to `+∞`), the existing "no overlapping periods" check already guarantees at most one open entry can exist at a time -- a separate "only one open entry" rule would just restate the same constraint differently, not add anything.

**Overlap checking happens in Python over all existing entries, not a single SQL range-overlap query.** Sensor-log entries number in the dozens even over a long MVP lifetime (a sensor lasts ~14 days); fetching the handful of rows and comparing in Python is simpler to read and test than a `tstzrange`/`daterange`-based SQL overlap query, for a table this small.

**Manual-entry UI is two plain routes, not one combined form.** `GET /sensor-log` (list existing entries + an "add new period" form) and `POST /sensor-log` (create) mirror the upload pages' GET-shows-form/POST-processes pattern exactly. Closing an entry is a separate `POST /sensor-log/{id}/close` (its own small form, rendered inline per open entry in the list) rather than overloading the create form, since the two actions take different fields and apply to different entries.

**Dashboard integration is a new `get_sensor_log_overlaps(db, start, end)` in `dashboard_data.py`**, returning the list of overlapping entries plus an unlogged-day count, following the same shape as `get_monthly_glucose_calendar`/`get_daily_glucose_profiles` (a pure query function consumed by `_dashboard_context`, rendered by a plain Jinja2 section in `dashboard_content.html` -- a list/table, not a calendar heatmap, since the spec only requires *showing* overlapping entries and an unlogged-day count, not a specific visual format).

## Risks / Trade-offs

- **The Python-side overlap check does not hold a database-level lock, so two concurrent submissions could both pass validation against the same stale read and both insert overlapping rows.** Acceptable for a single-user MVP with no concurrent writers in practice (the same accepted trade-off already made elsewhere in this codebase, e.g. medication-ingestion's upsert path); add a partial unique index or a `SELECT ... FOR UPDATE` guard only if this ever becomes a real multi-writer system.
