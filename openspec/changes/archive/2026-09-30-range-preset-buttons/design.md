# Design

## Context

`app/templates/dashboard_content.html` currently has a plain HTML form with two `<input type="date">` fields and an "Update" button, submitting via `hx-get="/dashboard"`. The user finds this impractical day-to-day and wants one-click presets instead.

## Goals / Non-Goals

**Goals:**
- Four one-click presets (7/14/30/90 days ending today), no separate confirm step.
- Keep the backend route's `start`/`end` query-parameter contract exactly as-is, so the existing test suite (which seeds specific dates and asserts against specific `start`/`end` combinations) and any future need for an exact custom range via a direct URL both keep working unchanged.

**Non-Goals:**
- A manual date picker for an arbitrary custom range -- explicitly what the user wants removed from the UI. The backend still accepts one via a direct URL (unchanged route contract), just nothing in the rendered page exposes it any more.
- Persisting the user's last-chosen preset across page loads/sessions (e.g. a cookie) -- out of scope; every fresh page load defaults to 30 days unless the URL itself carries a different range (e.g. from `hx-push-url`'s browser history).

## Decisions

**Compute the preset's start/end in client-side JS (`Date`), not server-side.** The radios need to fire an immediate request with concrete dates; computing them in the browser avoids a round-trip just to ask the server "what are the dates for a 7-day preset". Uses local `getFullYear`/`getMonth`/`getDate` (not `toISOString().slice(0,10)`, which is UTC and would reintroduce the exact day-boundary bug `mexico-city-local-time` just fixed) -- correct as long as the browser's own clock/timezone is set to the user's actual location, which it is for this single-user project.

**Fire the request via `htmx.ajax()` in a small JS function, not `hx-vals="js:..."`.** Both are supported by HTMX; a named JS function the four radios all call is more readable than four copies of an inline `js:` expression string, and keeps the computed-date logic in one place.

**Which preset is "active" is computed server-side, in `_dashboard_context`**, not client-side: compares the current `start`/`end` against today's America/Mexico_City date and each preset's span, so the page loads with the correct radio already checked (including on the very first visit, where the default 30-day range should show "30" selected) without a client-side flash of no selection.

**Fixed a real off-by-one in the default range while wiring this up.** `_resolve_range`'s default start was `end_dt - timedelta(days=30)`, which spans 31 calendar days inclusive, not 30 -- so the default range never matched the "30 days" preset's true 30-inclusive-day span, and the preset radio never showed as checked on first load. Changed to `timedelta(days=_DEFAULT_RANGE_DAYS - 1)` so the default range's span exactly equals the preset's.

**Backend route contract unchanged.** `_resolve_range`/`_dashboard_context` still take `start`/`end` strings exactly as before -- this change is a presentation-layer replacement, not a route redesign, so none of the existing `start`/`end`-based tests need to change, and nothing about how data is fetched or filtered changes.

## Risks / Trade-offs

- **A user whose browser clock/timezone is misconfigured** would compute a wrong "today" client-side -- accepted, since the same would already be true of any client-side date picker, and this is a single user on their own devices.
- **No way to pick an arbitrary custom range from the UI any more** -- explicitly what was asked for; the route itself still supports it for programmatic/direct-URL use.
