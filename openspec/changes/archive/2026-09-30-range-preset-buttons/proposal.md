# Proposal

## Why

The user finds the two `<input type="date">` pickers impractical for day-to-day use and wants one-click presets instead: last 7, 14, 30 or 90 days.

## What Changes

- Replace the manual "From"/"To" date-picker form with four radio buttons (7/14/30/90 days ending today), each immediately refreshing the dashboard via HTMX when selected -- no separate "Update" button needed.
- The radio matching the currently-viewed range (if any) is pre-selected on load; the default (no range selected) is 30 days, so it shows pre-selected on first visit.
- The backend route itself is unchanged: it still accepts arbitrary `start`/`end` query parameters. Only the production UI's way of setting them changes -- this keeps the existing test suite's precise-range assertions, and any future need for an arbitrary custom range via a direct URL, working exactly as before.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `dashboard`: the "Date-range filtering" requirement's selection mechanism changes from manual date pickers to four fixed presets.

## Impact

- **Changed code**: `app/templates/dashboard_content.html` (radio buttons + a small inline JS helper replacing the date-picker form), `app/routers/dashboard.py` (`_dashboard_context` computes which preset, if any, matches the current range, for pre-selecting the right radio).
- **No new dependency**: computes the preset's start/end client-side with plain JS `Date`, and fires the request via `htmx.ajax()` (already loaded, no new attribute-based HTMX trickery).
- **No database or route-contract changes.**
