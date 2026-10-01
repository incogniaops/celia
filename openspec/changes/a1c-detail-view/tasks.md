# Tasks

- [x] 1. In `get_glucose_summary_stats` (`app/dashboard_data.py`), add `gmi_mmol_mol` (DCCT-to-IFCC conversion), `days_with_data` (distinct calendar days with a reading) and `days_in_range` (inclusive day count of the range) to the returned dict.
- [x] 2. Unit tests: mmol/mol matches the report's own worked example (6.0% -> 42 mmol/mol), days_with_data/days_in_range for a range with gaps (fewer days with data than days in range) and a fully-covered range.
- [x] 3. Update the A1C card in `app/templates/dashboard_content.html` to show the mmol/mol equivalent and the "Data spans X of Y days" line.
- [x] 4. Integration test: dashboard's A1C card shows both units and the coverage line for a known slice of data.
- [x] 5. Verify end-to-end in the Podman container against the real glucose dataset for the exact range from the user's screenshot (3 Jul - 30 Sept 2026): day-coverage matched exactly ("61 of 90 days"); GMI was close but not identical (6.3%/45 mmol/mol vs the screenshot's 6.0%/42 mmol/mol) over this wider window, consistent with the approximation already documented in glucose-pattern-views (the narrower 17-30 Sept range previously matched exactly).
- [x] 6. Run `/changelogger` then `/commit` once verified.
