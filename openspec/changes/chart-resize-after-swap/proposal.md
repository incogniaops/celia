# Proposal

## Why

The user reports that after `range-preset-buttons` shipped, the glucose trend chart (and, intermittently, the AGP chart) sometimes renders squashed to a small fixed size (Chart.js's own 300x150 default) instead of filling its container, after clicking a range preset. Not every time -- "a veces" (sometimes).

## What Changes

- Defer each chart's `new Chart(...)` construction to the browser's next animation frame (`requestAnimationFrame`), instead of running synchronously the instant the swapped-in `<script>` tag executes.
- Call `.resize()` explicitly right after construction, as a second safety net.

## Capabilities

### Modified Capabilities
- `dashboard`: the "Responsive layout" requirement gains an explicit scenario for charts specifically, since this is a chart-sizing bug, not a general layout bug.

## Impact

- **Changed code**: `app/templates/dashboard_content.html` (both chart `<script>` blocks).
- **No new dependency** -- `requestAnimationFrame` is a standard browser API.
- **Honest limitation**: this is a browser-side rendering-timing bug (Chart.js measuring its container's size before the swapped-in DOM has finished layout), not something a curl-based or pytest-based check can reproduce or definitively prove fixed -- this change applies the standard, well-documented fix for exactly this class of "chart renders wrong size after an AJAX/innerHTML swap" issue, verified by confirming the app still renders correctly and has no regressions, but the intermittent symptom itself needs the user's own confirmation after clicking through the presets a few times in their actual browser.
