# Proposal

## Why

US-05 (data-sharing) has been specified since the MVP's original scope but never built, and OD-02 ("exact share mechanism: signed link vs. exported PDF/HTML file") has sat open the whole time blocking it. The user has now resolved OD-02: celia generates a downloadable PDF for a chosen date range, which the user prints or emails himself -- no link, no revocation, no in-app email sending. He wants it styled as an editorial, LaTeX-typeset clinical report, explicitly modelled on his own real LibreView "Informe del AGP" PDF (the report FreeStyle LibreLink/LibreView already produces from his Abbott sensor data), reusing data celia already computes for the dashboard rather than inventing a new data model.

## What Changes

- Add a PDF-export endpoint that renders the currently-selected dashboard date range as a single LaTeX-typeset PDF, compiled with Tectonic (a self-contained, modern TeX engine), reusing `dashboard_data.py`'s existing `get_glucose_summary_stats`, `get_agp_percentile_bands` and `get_current_biometric_profile`, plus a new per-day grouping of `get_glucose_trend`'s readings for the daily-profile grid (see design.md).
- The PDF's layout is modelled on the user's real LibreView AGP report (`data/abbott/RodrigoÁlvarez_30-09-2026.pdf`, page 1): a header (name, date range -- no birth date), a time-in-range box (stacked colour-coded band bar with percentages and targets), a glucose-stats box (average mg/dL, GMI % and mmol/mol, %CV), an AGP percentile-band chart, and a daily-glucose-profile grid (one sparkline per calendar day, grouped in week rows).
- **BREAKING (spec-level, not yet built so nothing to migrate):** removes the previously-specified share-*link* mechanism (a revocable, read-only URL) from `data-sharing`'s main spec, replacing it with the PDF-export mechanism. The two existing requirements describing link behaviour ("Read-only access for share recipients", "Revocable shares") are removed; nothing currently implements them.
- Deliberately does **not** replicate three things the real Abbott report has, each for a stated reason (see design.md): the patient's birth date/real age (celia's existing business rule never reveals it, even on shared views), the "% sensor time active" metric (depends on sensor-log/US-06, not yet built), and the second report page's automatic clinical pattern-detection commentary (that's Abbott's own clinical judgement, not something celia should approximate).

## Capabilities

### Modified Capabilities
- `data-sharing`: replaces the generic "read-only view (link) or export (file)" requirement with a concrete PDF-export requirement (LaTeX/Tectonic, Abbott-AGP-report-styled, covering the selected date range); removes the two link-specific requirements ("Read-only access for share recipients", "Revocable shares"), which described a mechanism this iteration does not build.

## Impact

- **New code:** a PDF-generation module (LaTeX template + Tectonic invocation), a new per-day glucose grouping helper in `app/dashboard_data.py`, and a new FastAPI route (likely `GET /dashboard/export.pdf` or similar, under `app/routers/dashboard.py`) accepting the same `start`/`end` query parameters the dashboard already uses.
- **New dependency:** Tectonic (a ~80 MB self-contained LaTeX engine binary) added to the Containerfile; no new Python package is strictly required if Tectonic is shelled out to directly, though a thin wrapper may be added.
- **Changed spec:** `openspec/specs/data-sharing/spec.md` (two requirements removed, one requirement rewritten, as above).
- **No changes** to existing ingestion, sync, or dashboard-rendering code -- this change only adds a new, read-only export path that reuses existing query functions.
