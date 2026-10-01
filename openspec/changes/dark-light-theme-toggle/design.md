# Design

## Context

Both `dashboard.html` and `dashboard_empty.html` currently hardcode `<html lang="en" data-theme="light">`. Pico.css (already the project's only CSS, loaded via CDN) reads `data-theme="dark"`/`"light"` on any ancestor element to pick its colour palette -- no new library needed, just driving that attribute dynamically instead of hardcoding it.

## Goals / Non-Goals

**Goals:**
- Dark by default, one click to switch, remembered across visits.
- No flash of the wrong theme on load.
- Survive the dashboard's HTMX range-preset swaps without re-running any setup (the toggle button and its script live in the static shell, outside the `#dashboard-content` div that swaps).
- The dashboard's own hardcoded colours -- the two Chart.js charts and the pastel-background "Time in range"/"Monthly glucose calendar" cells -- stay legible in both themes, since neither Pico.css nor Chart.js adapts those automatically.

**Non-Goals:**
- Theming the three upload pages -- they don't load Pico.css today and have no visual theme to toggle; adding one would be unrelated styling work, not part of this request.
- A server-side/account-level theme preference -- this is a single-user project opened from the same browser(s); `localStorage` is sufficient, no database column or API needed.
- Following the OS-level light/dark preference (`prefers-color-scheme`) -- the user asked for dark as the fixed default, not "match my system", so the stored preference (or dark, absent one) always wins.

## Decisions

**`localStorage`, not a cookie or a server round-trip.** The theme only affects client-side rendering (a CSS attribute), so there's no reason to involve the server at all -- reading/writing `localStorage` is synchronous and available before first paint.

**Theme-setting script placed first in `<head>`, before the Pico CSS `<link>`.** Setting `data-theme` on `<html>` has to happen before the browser applies Pico's stylesheet to avoid a flash of the default (light) theme followed by a flip to dark. A synchronous inline `<script>` early in `<head>` runs before the page paints, so this is sufficient without any library.

**Duplicated across the two templates, not factored into a shared base template.** This codebase has no Jinja `{% extends %}`/base-template pattern anywhere yet (each page is self-contained); introducing one for a ~10-line snippet would be a bigger structural change than the toggle itself. Matches the project's existing convention of small, page-local duplication (e.g. each dashboard chart script is its own self-contained block) over premature shared abstraction.

**Toggle button lives in the static shell of `dashboard.html`, outside `#dashboard-content`.** The date-range presets already swap only `#dashboard-content` via HTMX; keeping the toggle outside that div means it (and its already-applied theme) are untouched by every range-preset click, with nothing to re-initialise.

**Chart.js colours set explicitly per theme, not left as library defaults.** Chart.js's default tick/legend/gridline colours assume a light page background; they do not read Pico's `data-theme` attribute or any CSS variable. Two small helpers (`celiaChartTextColor()`, `celiaChartGridColor()`) read `document.documentElement.getAttribute("data-theme")` at chart-build time and return a light or dark-appropriate colour, passed into each chart's `options.color`, `scales.*.ticks.color`, `scales.*.grid.color` and `plugins.legend.labels.color`.

**Charts listen for a `celia-theme-change` custom event and rebuild, rather than leaving stale colours until the next HTMX swap.** `celiaToggleTheme()` dispatches that event after flipping `data-theme`; each chart's script destroys and rebuilds itself on the event, matching the pattern already used for the HTMX range-preset swap (`window.celiaGlucoseChart`/`window.celiaAgpChart` destroy-then-recreate). Without this, toggling the theme without also changing the date range would leave the charts' text in the old theme's colour until the next range-preset click.

**Pastel table/calendar cells get a fixed dark text colour, not a per-theme one.** The "Time in range" and "Monthly glucose calendar" cells' backgrounds (`#fecaca`, `#fed7aa`) are light pastels regardless of page theme, so a single dark text colour (`#7f1d1d` / `#7c2d12`, matching each background's hue) is legible against them in both dark and light mode -- simpler than branching text colour on `data-theme` for a background that itself never changes.

## Risks / Trade-offs

- **Two copies of the same small script** (one per template) -- accepted, see the no-base-template decision above.
- **Chart colour helpers and the theme-change listener add a small amount of per-chart boilerplate** (duplicated between the glucose-trend and AGP chart scripts) -- accepted for the same reason as the base-template decision above: this codebase favours small, page-local duplication over a shared abstraction for a handful of lines.
