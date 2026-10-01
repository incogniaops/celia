# Proposal

## Why

The user shared a screenshot of LibreView's own "A1C calculada" report screen: alongside the 6.0% figure (matching celia's own GMI card exactly), it shows the IFCC mmol/mol equivalent (42 mmol/mol) and a data-coverage disclosure ("Los datos abarcan 61 de 90 días"). The user chose to adopt both.

## What Changes

- Add the mmol/mol equivalent (IFCC units) next to the existing A1C (GMI) percentage.
- Add a data-coverage line: how many of the selected range's calendar days actually have at least one glucose reading, out of the total days in the range -- the same shape of disclosure LibreView's own report shows.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `dashboard`: the "Time-in-range and glucose-control summary" requirement's A1C card gains the mmol/mol equivalent and a data-coverage line.

## Impact

- **Changed code**: `app/dashboard_data.py` (`get_glucose_summary_stats` gains `gmi_mmol_mol`, `days_with_data`, `days_in_range`), `app/templates/dashboard_content.html` (A1C card).
- **No database changes, no new dependency** -- the mmol/mol conversion is a fixed formula, the day-coverage count is a simple aggregation over data already fetched.
