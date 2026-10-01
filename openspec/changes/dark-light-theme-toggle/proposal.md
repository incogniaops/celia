# Proposal

## Why

The user wants to switch between dark and light theme, with dark as the default. The dashboard currently hardcodes `data-theme="light"`.

## What Changes

- Add a small toggle button to the two Pico.css-styled pages (`dashboard.html`, `dashboard_empty.html`) that switches `<html data-theme>` between `dark` and `light`.
- Default to `dark` when the user has no stored preference.
- Persist the choice in the browser (`localStorage`), so it survives reloads and HTMX-driven range-preset refreshes without needing a server round-trip.
- Apply the stored/default theme before first paint, to avoid a flash of the wrong theme.
- Make the dashboard's own hardcoded colours theme-aware, since neither Pico.css nor Chart.js adapts them automatically:
  - The "Time in range" table and "Monthly glucose calendar" cells use fixed pastel backgrounds (`#fecaca`, `#fed7aa`); those cells now also pin a fixed dark text colour, so they stay legible against either theme instead of inheriting the page's light-on-dark default text colour.
  - The two Chart.js charts (glucose trend, ambulatory glucose profile) read the current `data-theme` and set their own tick, legend and gridline colours accordingly -- Chart.js has no built-in page-theme awareness and otherwise renders dark, near-invisible text/gridlines on the dark background. Both charts redraw with the new colours when the user toggles, via a `celia-theme-change` event.

## Capabilities

### Modified Capabilities
- `dashboard`: adds a theme-toggle requirement, and a legibility requirement for the charts and hardcoded-colour table/calendar cells under both themes.

## Impact

- **Changed code**: `app/templates/dashboard.html`, `app/templates/dashboard_empty.html` (both gain the same small inline script + toggle button); `app/templates/dashboard_content.html` (theme-aware chart colours, fixed-contrast table/calendar text colours).
- **No new dependency**: plain `localStorage` and a `data-theme` attribute, both already how Pico.css's own theming works (the project already set `data-theme="light"` by hand).
- **Scoped to the two Pico-styled pages only.** The three upload pages (`upload_libre.html`, `upload_mytherapy.html`, `upload_wyze.html`) don't load Pico.css at all today and have no visual theme to toggle -- adding one there would be unrelated styling work, not part of this request.
