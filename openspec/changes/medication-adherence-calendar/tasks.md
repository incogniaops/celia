# Tasks

- [x] 1. Add a `get_medication_adherence_calendar(db, start, end)` function to `app/dashboard_data.py`: reuse `get_medication_doses_in_range`, group doses by `(name, actual_date.date())`, apply the "any rejected wins" consolidation rule, and return a structure of distinct medication names (sorted) × every day in `[start, end]` with a per-cell status (`confirmed` / `rejected` / `None` for no dose scheduled).
- [x] 2. Unit tests for the grouping function: multiple doses same day same status, multiple doses same day with a mix (rejected wins), a day with no dose for a medication that has doses on other days, a medication with doses only outside the range excluded from rows.
- [x] 3. Replace the medication `<article>` block in `app/templates/dashboard_content.html` with a calendar table (rows = medication names, columns = days, cells = status symbol) plus a short text legend, using existing Pico.css table styling only — no new CSS/palette.
- [x] 4. Wire the new data into `app/routers/dashboard.py`'s `_dashboard_context`, replacing `medications` with the calendar structure (or adding alongside, if any other part of the codebase reads `medications` — check before removing).
- [x] 5. Integration test: dashboard route renders the calendar table correctly for a known slice of real-shaped medication data.
- [x] 6. Verify end-to-end against the real 466 medication doses in the Podman container: run the dashboard, confirm the calendar matches the underlying data for a sample medication and date range.
- [x] 7. Run `/changelogger` then `/commit` once verified.
