# Tasks

- [x] 1. Wrap the `glucose-chart` script's `new Chart(...)` call in `requestAnimationFrame`, with an explicit `.resize()` call right after construction.
- [x] 2. Apply the same change to the `agp-chart` script.
- [x] 3. Verified in the Podman container: full test suite still passes (118/118, no regressions expected for a template/JS-only change), both the full-page load and an HTMX fragment response render the rAF-wrapped scripts with no server errors. As stated in design.md, the intermittent sizing bug itself cannot be reproduced or disproven from this environment (no real browser here) -- needs the user's own confirmation after clicking through the presets a few times.
- [x] 4. Run `/changelogger` then `/commit` once verified.
