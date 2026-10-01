# Proposal

## Why

The user wants to switch between dark and light theme, with dark as the default. The dashboard currently hardcodes `data-theme="light"`.

## What Changes

- Add a small toggle button to the two Pico.css-styled pages (`dashboard.html`, `dashboard_empty.html`) that switches `<html data-theme>` between `dark` and `light`.
- Default to `dark` when the user has no stored preference.
- Persist the choice in the browser (`localStorage`), so it survives reloads and HTMX-driven range-preset refreshes without needing a server round-trip.
- Apply the stored/default theme before first paint, to avoid a flash of the wrong theme.

## Capabilities

### Modified Capabilities
- `dashboard`: adds a theme-toggle requirement.

## Impact

- **Changed code**: `app/templates/dashboard.html`, `app/templates/dashboard_empty.html` (both gain the same small inline script + toggle button).
- **No new dependency**: plain `localStorage` and a `data-theme` attribute, both already how Pico.css's own theming works (the project already set `data-theme="light"` by hand).
- **Scoped to the two Pico-styled pages only.** The three upload pages (`upload_libre.html`, `upload_mytherapy.html`, `upload_wyze.html`) don't load Pico.css at all today and have no visual theme to toggle -- adding one there would be unrelated styling work, not part of this request.
