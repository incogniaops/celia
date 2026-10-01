# Tasks

- [x] 1. Add `app/parsers/wyze.py`: `sniff_file_type`, and `parse_wyze_export(content: bytes) -> ParsedBodyCompositionExport` that reads the first sheet only (via `xl/workbook.xml` order, not sheet name), splits it into its named sections (title-row detection, not hardcoded row numbers), strips unit suffixes, converts lb fields to kg, skips `"- -"` placeholders, parses the optional "Heart Rate" section into `heart_rate` data points, and returns one `health_metrics`-ready dict per (row, present field) pair.
- [x] 2. Unit tests for the parser using the real sample file (`data/wyze/scaledata_300926.xlsx`): full bioimpedance row produces all fields, quick-weigh row (`"- -"` fields) produces only weight/BMI, the second sheet's data is never returned, unit conversion is correct (lb->kg fields), the Heart Rate section's reading is parsed as `heart_rate`, an export without a Heart Rate section still ingests normally, and an unrecognised file is rejected.
- [x] 3. Add `POST /uploads/wyze` and `GET /uploads/wyze` to `app/routers/uploads.py`, mirroring the Libre/MyTherapy upload routes, calling `insert_health_metrics` with the parsed data points.
- [x] 4. Add `app/templates/upload_wyze.html` and `upload_wyze_result.html`, mirroring the existing upload form/result templates; add the Wyze upload link to `app/templates/dashboard_empty.html`.
- [x] 5. Integration test: uploading the real sample file via `/uploads/wyze` stores the expected number of health-metrics rows, and re-uploading it produces no duplicates.
- [x] 6. Add `muscle_mass` to `BIOMETRIC_METRIC_TYPES` in `app/dashboard_data.py` so it appears in `get_current_biometric_profile` alongside the existing four.
- [x] 7. Add an "A1C (estimated)" card to `app/templates/dashboard_content.html`'s biometric-cards section, driven by `glucose_summary.gmi_percent`; remove the GMI line from the time-in-range summary's text (keep average and %CV there).
- [x] 8. Integration test: dashboard shows a muscle-mass card and an A1C card when the relevant data exists, and omits the A1C card when there's no glucose data in range.
- [x] 9. Verify end-to-end in the Podman container: upload the real Wyze export, confirm the muscle-mass and A1C cards render with values consistent with the source file and the already-verified GMI calculation.
- [x] 10. Run `/changelogger` then `/commit` once verified.
