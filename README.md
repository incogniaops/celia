# celia

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Status: Engineering Ready](https://img.shields.io/badge/status-Engineering%20Ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.12%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-D71F00)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![HTMX](https://img.shields.io/badge/HTMX-2.0-3D72D7)
![Chart.js](https://img.shields.io/badge/Chart.js-via%20CDN-FF6384?logo=chartdotjs&logoColor=white)
![Podman](https://img.shields.io/badge/Podman%2FDocker-OCI--compliant-892CA0?logo=podman&logoColor=white)

A self-hosted health dashboard that brings a single person's diabetes-related data together in one place, so it can be reviewed and shared without depending on separate, closed vendor ecosystems.

## Why celia

Diabetes management data is normally split across several closed systems: FreeStyle Libre glucose readings in LibreView, medication adherence in MyTherapy, weight/vitals/activity data from a Wyze scale and a Xiaomi smartband (reachable through the Google Health API), and the Wyze scale's own body-composition fields (muscle mass, body water, metabolic age and more) that Google Health doesn't expose at all. None of them talk to each other, so preparing for a doctor's appointment means manually reconstructing the full picture from several different apps.

celia ingests exports and API data from these sources, aligns them by date and time, and shows them together on one responsive screen — usable from a desktop or a mobile browser — that can be shared read-only with a doctor in under a minute.

The name is a nod to Celia Cruz and her song "Azúcar" — a play on *azúcar* (sugar/blood glucose) fitting the theme.

## Origin

celia started as a personal project for the México Tech Hub SDD (Spec-Driven Development) Hackathon (2026-09-21 to 2026-10-02), built independently of the hackathon's official team assignments, under Rodrigo Álvarez's own token budget for the event.

## What's built

All four data sources are ingested and verified end-to-end against real data:

- **FreeStyle Libre** (CSV and/or PDF export from LibreView) — glucose readings, the sole glucose source.
- **MyTherapy** (CSV archive or monthly PDF report) — medication-adherence data.
- **Google Health API** — weight, body fat, heart rate, resting heart rate, steps and sleep, fed by a Wyze scale and a Xiaomi smartband via Health Connect.
- **Wyze body-composition export** (`.xlsx`, uploaded) — muscle mass, BMI, body water, bone mass, metabolic age and other fields Google Health doesn't expose, plus its own weight/body-fat/heart-rate readings.

The consolidated dashboard shows, for a chosen date range (one-click 7/14/30/90-day presets):

- A glucose trend chart with insulin/carbohydrate markers.
- A medication-adherence calendar (one row per medication, one column per day).
- Glucose pattern views: a time-in-range summary, an ambulatory glucose profile (AGP) chart, and a monthly glucose calendar.
- A biometric-and-glucose-summary card row: metabolic-age delta, weight, body fat, BMI, glucose average/%CV and estimated A1C (GMI) — the card row never reveals the user's real chronological age, only the signed delta against metabolic age.
- A dark/light theme toggle (dark by default), legible in both themes including the charts and the colour-coded table/calendar cells.

**Not yet built:** sharing a read-only view with a doctor (US-05), and the manually-maintained FreeStyle Libre sensor log (US-06). Both remain fully specified but unimplemented.

The full specification — the anchor for what celia is and does, including user stories, business rules, quality attributes and open decisions — is in [`docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md`](docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md). Capability-level behaviour contracts derived from it live under [`openspec/specs/`](openspec/specs/).

**Data shared with doctors is sensitive:** biometric profile (weight, body fat, heart rate, resting heart rate), glucose data and medication data are all normally private. The author knowingly includes them in celia and in what he shares, to give his doctors a fuller picture — see the specification's Q-05 for how this data must be protected.

Single-user in the MVP, with the architecture kept open to grow (additional patients, doctor accounts) in a later iteration. Apple Health integration is deferred to a later iteration.

## Deployment

celia is self-hosted on the author's own homelab, as a container:

- **Runtime:** a single VM running Podman or Docker (OS still to be decided between Fedora and Ubuntu).
- **Local development:** Podman on macOS.
- **Future iteration:** a possible move to Kubernetes on Talos Linux with containerd. The container image is kept strictly OCI-compliant so it runs unchanged across all of these.

## Status

Hackathon MVP, specification **Engineering Ready** (v1.2). All seven user stories (US-01 – US-07) are specified; five are built and verified end-to-end against real data (ingestion from all four sources, plus the full consolidated dashboard). Sharing (US-05) and the sensor log (US-06) remain specified but not yet built. See the specification's Open Decisions section (mainly OD-01b, the VM's operating system, and OD-02, the exact share mechanism) for what's still open.

## Acknowledgements

celia was built using Claude tokens and the development environment Elsevier authorised for the México Tech Hub SDD Hackathon. The self-hosted deployment infrastructure, the personal domain, and the underlying health data — normally private — are the author's own, contributed as part of this project.

---

*This project was developed by Rodrigo Álvarez and is distributed under the MIT Licence. See the [LICENSE](LICENSE) file for details.*

*Copyright © 2026, Elsevier.*
