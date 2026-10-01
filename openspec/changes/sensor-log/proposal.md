# Proposal

## Why

US-06 is the last unbuilt user story (all of US-01–US-05 and US-07 are built and verified against real data). It is also celia's one deliberate exception to "no manual data entry": sensor lifetimes vary in practice (some fail early), so gaps in the glucose timeline alone can't reliably signal a sensor change, and FreeStyle Libre's own "Estado" status code is undocumented by Abbott but still worth capturing for the user's own reference. The main `sensor-log` spec (`openspec/specs/sensor-log/spec.md`) is already fully written from earlier planning; this change builds it.

## What Changes

- Add a `sensor_log_entries` table (serial, start date, start status code, nullable end date, nullable end status code) and an Alembic migration, following this codebase's existing per-capability-table pattern (`glucose_readings`, `medication_doses`, `health_metrics`).
- Add a simple HTML form (no JS framework, matching the upload pages' plain-form style, not the HTMX dashboard) to record a new open-ended sensor period, and a separate action to close an open entry with its end date and end status code (which may be left blank if the sensor has aged out of the FreeStyle LibreLink app's "last 3 sensors" list).
- Reject a new entry whose date range would overlap an existing one, naming the conflicting entry.
- Add a "Sensor log" section to the dashboard showing which sensor-log entries overlap the currently-selected date range, and how many days in that range have no matching entry (unlogged), without blocking the rest of the dashboard.
- Store the "Estado" status code as an opaque string; never interpret or decode it.

## Capabilities

### Modified Capabilities
- `dashboard`: adds a requirement for the new "Sensor log" section (which sensors overlap the selected range, unlogged-day count), since this is new dashboard-level behaviour not previously specified anywhere.

`sensor-log` itself is deliberately **not** listed here: its main spec (`openspec/specs/sensor-log/spec.md`) was fully written during earlier planning and its requirements do not change -- this change only builds what that spec already describes. A delta spec exists solely to carry a behaviour *change*; since there is none, no `specs/sensor-log/` delta is created, and archiving this change later has nothing to sync for that capability.

## Impact

- **New code:** `SensorLogEntry` model + migration, a repository function for overlap-checked inserts, a new router (`app/routers/sensor_log.py`) with GET/POST routes for recording and closing entries, two new plain-HTML templates, and a new `get_sensor_log_overlaps` (or similarly named) function in `dashboard_data.py` plus a new dashboard-template section.
- **No new dependency:** plain HTML forms, same stack as the existing upload pages.
- **No changes** to any other capability's ingestion, sync, or stored data.
