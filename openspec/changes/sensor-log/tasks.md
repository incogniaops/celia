# Tasks

## 1. Data model

- [x] 1.1 Add `SensorLogEntry` to `app/models.py` (`serial`, `start_date`, `start_status_code` required; `end_date`, `end_status_code` nullable, all as described in design.md) and generate the Alembic migration; verify `alembic upgrade head` creates `sensor_log_entries` in the real dev database with the expected columns.
- [x] 1.2 Add `insert_sensor_log_entry(db, entry)` and `close_sensor_log_entry(db, entry_id, end_date, end_status_code)` to `app/repository.py`, with the Python-side overlap check (design.md) applied only on insert; verify with a quick script against the real dev database that an overlapping insert is rejected and names the conflicting entry, a non-overlapping insert succeeds, and closing an open entry succeeds without re-checking overlap.

## 2. Manual-entry routes and templates

- [x] 2.1 Add `app/routers/sensor_log.py` with `GET /sensor-log` (list existing entries, newest first, plus an "add new period" form) and `POST /sensor-log` (create, rejecting an overlap with a clear error instead of a 500); register the router in `app/main.py`; verify by curling both routes against the real dev database.
- [x] 2.2 Add `POST /sensor-log/{id}/close` (end date, optional end status code) and an inline close-form per open entry in the list template; verify closing a real open entry in the dev database updates it and leaves closed entries unaffected.
- [x] 2.3 Add the two templates (`sensor_log.html` for the list+forms, matching the upload pages' plain HTMX-posted-form style, no Pico CSS); verify server-side that the rendered list reflects real inserted/closed entries. (Built as one combined list+both-forms template rather than two, since the "close" form is per-row inline, not a separate page -- recorded here as a minor, non-behaviour-affecting implementation detail, not a scope change.)

## 3. Dashboard integration

- [x] 3.1 Add `get_sensor_log_overlaps(db, start, end)` to `app/dashboard_data.py`, returning the entries overlapping the range and the count of unlogged days in it (design.md); verify against the real dev database for a range with a mix of logged and unlogged days, and for the before-any-entries-exist case.
- [x] 3.2 Wire it into `_dashboard_context` and add a "Sensor log" section to `dashboard_content.html` (a list of overlapping entries plus the unlogged-day count); verify end-to-end in the Podman container that the section renders correctly for both the empty-log and some-entries cases, and that it doesn't block any other dashboard section when the log is empty. (Verified against the real dev database via a local server, not yet rebuilt into the Podman image -- that happens in task 4.1.)

## 4. End-to-end verification

- [x] 4.1 Record and close at least one real sensor period against the real dev database in the Podman container (using this user's own FreeStyle LibreLink "Acerca de" status codes if available), and confirm it appears correctly in both `/sensor-log` and the dashboard's "Sensor log" section for a range that overlaps it. Verified functionally with a placeholder entry (recording the user's actual sensor history is itself the manual-entry action the user performs, not something to fabricate on their behalf); removed the placeholder entry afterward.
- [x] 4.2 Run `/changelogger` then `/commit` once this is verified.
