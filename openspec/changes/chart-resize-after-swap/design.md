# Design

## Context

Both chart scripts (`glucose-chart`, `agp-chart` in `app/templates/dashboard_content.html`) run as an inline `<script>` immediately following their `<canvas>`, executed as soon as HTMX processes the swapped-in fragment. `new Chart(ctx, {responsive: true, maintainAspectRatio: false, ...})` measures its canvas's parent container's size *synchronously*, at construction time, to size the canvas. If that measurement happens before the browser has completed layout for the just-inserted DOM (a known, well-documented class of bug for charting libraries used after an AJAX/innerHTML swap), Chart.js falls back to its own built-in default canvas size (300x150) -- matching exactly what the user's screenshot shows (a small, fixed-looking chart instead of one filling its `.chart-wrap` container). Nothing resizes it back afterward, since Chart.js's responsive behaviour relies on a `ResizeObserver` on the container, which only fires on a subsequent *change* in size, not a one-off incorrect initial read.

## Goals / Non-Goals

**Goals:**
- Stop charts from locking in a wrong size when constructed before the swapped-in layout has settled.

**Non-Goals:**
- Root-causing the exact browser-internal timing (whether it's HTMX's swap/settle scheduling, or just generic layout-not-flushed-yet timing) -- not practically diagnosable from this environment (no interactive browser/devtools access here), and not necessary: `requestAnimationFrame` is the correct, standard fix regardless of the precise cause, since it guarantees running after the next completed layout/paint pass.
- A general "all charts always perfectly reliable" guarantee -- this fixes the specific, well-understood failure mode described, not an open-ended robustness audit.

## Decisions

**`requestAnimationFrame(() => { ...chart construction... })`, not a fixed `setTimeout` delay.** `requestAnimationFrame` runs its callback right before the browser's next paint, after the current layout pass has been computed -- the correct primitive for "wait until layout has settled", unlike a `setTimeout` guess that could still race on a slow device or be unnecessarily slow on a fast one.

**Also call `.resize()` right after construction**, as a cheap second safety net -- forces Chart.js to re-measure its container immediately, in case the very first paint after swap still raced with something else (e.g. a CSS transition/reflow not yet finished even by the next animation frame).

**No automated test for the intermittent symptom itself.** This is a browser rendering-timing issue; neither `curl`-based container verification nor pytest (no real browser/layout engine in that path) can reproduce or disprove it. Verification here is: confirm the app still renders correctly end-to-end (no JS syntax errors, no regressions in existing behaviour), and ask the user to confirm the fix empirically by clicking through the presets several times in their own browser -- the only environment where the original bug was observed.

## Risks / Trade-offs

- **Unverifiable by this project's existing automated checks.** Accepted and stated explicitly, rather than silently claiming a fix that can't actually be proven from here.
