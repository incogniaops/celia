# Design

## Context

Real MyTherapy PDF reports (`data/mytherapy/MyTherapy_2026_09.pdf`, page 3) show a "Historial de medicamentos" table: rows are medications, columns are days 1–30, cells hold a status icon (✅ confirmed, ✕ omitted, ⏸ interrupted, etc.), with a legend below. `medication_doses` (see medication-ingestion) already has everything needed to build this: one row per recorded dose, with `actual_date` (full timestamp), `name`, and `status` (`confirmed`/`rejected`).

## Goals / Non-Goals

**Goals:**
- Replace the flat medication list with a medication × day calendar for the dashboard's selected date range.
- Reuse the existing colour palette (Pico.css defaults) — no broader visual redesign, per the user's explicit choice of the narrowest of three options offered.

**Non-Goals:**
- Matching MyTherapy's exact per-scheduled-time granularity (e.g. two stacked rows for a twice-daily medication). This change consolidates to one row per medication per day (see the spec delta's second scenario).
- Matching MyTherapy's broader visual style (colours, typography, the peso/pasos-style summary-table-next-to-chart layout) — explicitly out of scope per the user's choice; a separate future change if wanted.
- Scrolling/pagination for very wide date ranges (e.g. 90+ days) — the existing 30-day default keeps the table a reasonable width; a very wide manually-selected range may not fit well, and that's accepted for now, not solved here.

## Decisions

**Consolidation key: (medication name, calendar day)**, not (medication name, scheduled time). `get_medication_doses_in_range` already returns every dose row for the range; grouping happens in Python (not SQL) since the data volume is small (hundreds of rows) and the grouping logic (day-level status consolidation) is easier to express and test as plain Python than as a window function.

**Status consolidation rule**: for a given (medication, day) with multiple doses, if *any* dose that day is `rejected`, the day shows as not-adhered; only if *all* doses that day are `confirmed` does it show as adhered. This errs toward surfacing a missed dose rather than hiding it behind a fully-adhered day — consistent with the product's purpose (something to actually show a doctor).

**Table shape**: rows = distinct medication names with at least one dose in the range (sorted alphabetically, not by first-dose-date, for a stable/scannable order across range changes); columns = every calendar day in the range (not just days with data), so gaps are visible as genuinely empty cells rather than a compressed timeline.

**Cell rendering**: a simple character/emoji per status (✅ adhered, ❌ not adhered, — no dose scheduled) rather than icons requiring an image asset, keeping the "no build step, CDN or inline only" pattern the rest of the app already follows. A text legend below the table explains the three states, mirroring MyTherapy's own legend.

## Risks / Trade-offs

- **Wide date ranges produce a wide table**: not addressed here (Non-Goals) — acceptable given the 30-day default, revisit if it proves a real problem once used day to day.
- **Consolidating multiple doses/day loses the specific missed time**: a user with a twice-daily medication who missed only the evening dose sees the whole day marked as not-adhered, without saying which dose. Accepted trade-off for a simpler table; the existing "Insulin & carbohydrates"-style flat list could be extended to show exact miss times later if this proves insufficient.
