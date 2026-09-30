# Changelog

## [2026-09-30] - Finalise MVP specification and adopt OpenSpec

- chore: require the changelogger and commit skills within OpenSpec's apply and archive operations guidance, so no change is applied or archived without a CHANGELOG.md entry and a proper commit
- feat: confirm Google Health API integration for weight, body fat, heart rate, resting heart rate, steps and sleep, sourced from a Wyze scale and a Xiaomi smartband via Health Connect
- feat: confirm MyTherapy CSV export as the preferred medication-adherence source, with the monthly PDF report as fallback
- feat: add a manual sensor log (US-06) as the sole exception to "no manual data entry", to track FreeStyle Libre sensor periods whose lifespans vary in practice
- docs: mark docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md as Engineering Ready (v1.1) after validating all three MVP data sources against real data
- chore: adopt OpenSpec for spec-driven development; add six capability specs under openspec/specs/ derived from the product specification's user stories
- chore: protect data/ and .secrets/ via .gitignore before any real health data or credentials could be committed

## [2026-09-29] - Initialise repository and licensing

- chore: initialise git repository with an SSH remote and the laboral identity
- docs: add the MIT LICENSE and a README with the project description and acknowledgements
- docs: draft the initial product specification (PS-CELIA-001) for the self-hosted diabetes dashboard MVP
