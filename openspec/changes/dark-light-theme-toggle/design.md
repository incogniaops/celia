# Design

## Context

Both `dashboard.html` and `dashboard_empty.html` currently hardcode `<html lang="en" data-theme="light">`. Pico.css (already the project's only CSS, loaded via CDN) reads `data-theme="dark"`/`"light"` on any ancestor element to pick its colour palette -- no new library needed, just driving that attribute dynamically instead of hardcoding it.

## Goals / Non-Goals

**Goals:**
- Dark by default, one click to switch, remembered across visits.
- No flash of the wrong theme on load.
- Survive the dashboard's HTMX range-preset swaps without re-running any setup (the toggle button and its script live in the static shell, outside the `#dashboard-content` div that swaps).

**Non-Goals:**
- Theming the three upload pages -- they don't load Pico.css today and have no visual theme to toggle; adding one would be unrelated styling work, not part of this request.
- A server-side/account-level theme preference -- this is a single-user project opened from the same browser(s); `localStorage` is sufficient, no database column or API needed.
- Following the OS-level light/dark preference (`prefers-color-scheme`) -- the user asked for dark as the fixed default, not "match my system", so the stored preference (or dark, absent one) always wins.

## Decisions

**`localStorage`, not a cookie or a server round-trip.** The theme only affects client-side rendering (a CSS attribute), so there's no reason to involve the server at all -- reading/writing `localStorage` is synchronous and available before first paint.

**Theme-setting script placed first in `<head>`, before the Pico CSS `<link>`.** Setting `data-theme` on `<html>` has to happen before the browser applies Pico's stylesheet to avoid a flash of the default (light) theme followed by a flip to dark. A synchronous inline `<script>` early in `<head>` runs before the page paints, so this is sufficient without any library.

**Duplicated across the two templates, not factored into a shared base template.** This codebase has no Jinja `{% extends %}`/base-template pattern anywhere yet (each page is self-contained); introducing one for a ~10-line snippet would be a bigger structural change than the toggle itself. Matches the project's existing convention of small, page-local duplication (e.g. each dashboard chart script is its own self-contained block) over premature shared abstraction.

**Toggle button lives in the static shell of `dashboard.html`, outside `#dashboard-content`.** The date-range presets already swap only `#dashboard-content` via HTMX; keeping the toggle outside that div means it (and its already-applied theme) are untouched by every range-preset click, with nothing to re-initialise.

## Risks / Trade-offs

- **Two copies of the same small script** (one per template) -- accepted, see the no-base-template decision above.
