# Tasks

- [x] 1. Add the theme-init script (reads `localStorage`, defaults to `dark`, sets `data-theme` on `<html>`) to the top of `<head>` in `dashboard.html` and `dashboard_empty.html`, before the Pico CSS `<link>`; remove the hardcoded `data-theme="light"` from both `<html>` tags.
- [x] 2. Add a small toggle button and its `celiaToggleTheme()` script to the static shell of both templates (outside `#dashboard-content` in `dashboard.html`, so it survives HTMX swaps).
- [x] 3. Verified server-side against the real Podman container: the theme-init script and toggle button render exactly once in the full page response, and are absent from the HTMX fragment response (confirming no duplication across range-preset swaps); no server errors. The actual flash-free rendering and click-to-toggle behaviour are real-browser-only concerns this environment has no browser automation for (same limitation as `chart-resize-after-swap`) -- needs the user's own confirmation in their browser.
- [x] 4. Run `/changelogger` then `/commit` once verified.
