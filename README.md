# celia

A self-hosted health dashboard that brings a single person's diabetes-related data together in one place, so it can be reviewed and shared without depending on separate, closed vendor ecosystems.

## Why celia

Diabetes management data is normally split across several closed systems: FreeStyle Libre glucose readings in LibreView, medication adherence in MyTherapy, and weight/vitals/activity data from a Wyze scale and a Xiaomi smartband, reachable through the Google Health API. None of them talk to each other, so preparing for a doctor's appointment means manually reconstructing the full picture from three different apps.

celia ingests exports and API data from these sources, aligns them by date and time, and shows them together on one responsive screen — usable from a desktop or a mobile browser — that can be shared read-only with a doctor in under a minute.

The name is a nod to Celia Cruz and her song "Azúcar" — a play on *azúcar* (sugar/blood glucose) fitting the theme.

## Origin

celia started as a personal project for the México Tech Hub SDD (Spec-Driven Development) Hackathon (2026-09-21 to 2026-10-02), built independently of the hackathon's official team assignments, under Rodrigo Álvarez's own token budget for the event.

## Scope (MVP)

- Ingest a FreeStyle Libre export from LibreView (CSV and/or PDF report) — the sole glucose source.
- Ingest a MyTherapy export (CSV preferred — a full-history archive, not just one month; monthly PDF report as fallback) for medication-adherence data.
- Sync weight, body fat, heart rate, resting heart rate, steps and sleep (Wyze scale, Xiaomi smartband) from the Google Health API. This requires two one-time setup steps beyond normal OAuth: linking the account at `fitbit.google.com/auth/signup`, and connecting Health Connect inside the Google Health app (Connections → Partner apps) — only the second step actually surfaces third-party data. Historical backfill is partial and varies by data type; steps and sleep also need pagination to retrieve more than the most recent page.
- No manual data entry: all data enters celia only through uploaded exports or API sync.
- A consolidated, responsive dashboard (desktop and mobile browsers).
- A read-only view or export for sharing with a doctor, without giving them an account.
- A manually-maintained sensor log (serial, start/end dates, start/end status codes) for FreeStyle Libre sensors — the one deliberate exception to "no manual data entry", since sensor lifespans vary in practice (some fail early) and gaps in the glucose timeline aren't a reliable signal of a sensor change on their own. The status codes help spot sensors that failed early.

**Data shared with doctors is sensitive:** biometric profile (weight, body fat, heart rate, resting heart rate), glucose data and medication data are all normally private. The author knowingly includes them in celia and in what he shares, to give his doctors a fuller picture — see the specification's Q-05 for how this data must be protected.

Single-user in the MVP, with the architecture kept open to grow (additional patients, doctor accounts) in a later iteration. Apple Health integration is deferred to a later iteration.

The full specification, including user stories, business rules, quality attributes and open decisions, is in [`docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md`](docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md).

## Deployment

celia is self-hosted on the author's own homelab, as a container:

- **Runtime:** a single VM running Podman or Docker (OS still to be decided between Fedora and Ubuntu).
- **Local development:** Podman on macOS.
- **Future iteration:** a possible move to Kubernetes on Talos Linux with containerd. The container image is kept strictly OCI-compliant so it runs unchanged across all of these.

## Status

Hackathon MVP. Specification is **Engineering Ready**: all three data sources (LibreView, MyTherapy, Google Health) have real data in hand and/or verified working. See the specification's Open Decisions section for what's still open (mainly the exact share mechanism) before a full build.

## Acknowledgements

celia was built using Claude tokens and the development environment Elsevier authorised for the México Tech Hub SDD Hackathon. The self-hosted deployment infrastructure, the personal domain, and the underlying health data — normally private — are the author's own, contributed as part of this project.

---

*This project was developed by Rodrigo Álvarez and is distributed under the MIT Licence. See the LICENSE file for details.*

*Copyright © 2026, Elsevier.*
