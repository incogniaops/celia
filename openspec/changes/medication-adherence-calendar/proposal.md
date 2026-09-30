# Proposal

## Why

The user reviewed real MyTherapy PDF reports (`data/mytherapy/`) as a design reference after finding the current dashboard's medication list too plain. MyTherapy's own monthly report presents adherence as a medication × day-of-month calendar (one row per medication, one column per day, a status icon per cell, with a legend) — a much clearer at-a-glance view than a flat chronological list, and it's a pattern already proven for exactly this data.

## What Changes

- Replace the dashboard's medication section (currently a flat `<ul>` of doses) with a medication-adherence calendar: rows are distinct medication names with at least one dose in the selected range, columns are each day in the range, cells show a confirmed/rejected/no-dose-scheduled status.
- Keep the current colour palette (Pico.css defaults) — this change is about the adherence view's structure, not a broader visual redesign (the user chose the narrowest of three options offered).

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `dashboard`: add a requirement for the medication-adherence calendar view, replacing the existing flat list as how medication doses are shown for the selected range. This changes the dashboard requirement's stated behaviour (was: "medication-adherence markers aligned to the same timeline" shown as a list), so it's a MODIFIED requirement, not just an addition.

## Impact

- **Changed code**: `app/dashboard_data.py` (new query/grouping function), `app/templates/dashboard_content.html` (calendar table replaces the `<ul>`).
- **No database changes.**
- **Simplification acknowledged upfront (see design.md)**: MyTherapy's own report shows one row *per scheduled time* for a medication taken more than once a day (e.g. two stacked icon rows for a twice-daily dose). This change consolidates to one row per medication per day instead — a deliberate simplification, not a silent gap.
