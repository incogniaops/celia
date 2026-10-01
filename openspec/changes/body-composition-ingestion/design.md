# Design

## Context

The user's real Wyze export (`data/wyze/scaledata_300926.xlsx`) is a "Body Composition Data" sheet: header row with `Number, Date and Time, Weight(lb), Weight(kg), BMI, Body Fat, Muscle Mass, Muscle Mass %, Body Water, Lean Body Mass, Bone Mass, Protein, Visceral Fat, BMR, Metabolic Age, Skeletal Muscle Rate %, Fat Content, Subcutaneous Fat`, one data row per weigh-in, 40 rows in the sample. The file has two sheets (`incognia@gmail.com` and `Julieta `) -- the user confirmed only the first (their own) should ever be ingested; the second is someone else's data recorded on the same physical scale.

Inspecting the file directly (`unzip` + reading `xl/worksheets/sheet1.xml`) shows cell values are inline strings (`t="inlineStr"`), not shared strings, with unit suffixes baked into the text (`"113.0kg"`, `"34.4%"`) and a `"- -"` placeholder for any bioimpedance field the scale couldn't read (present alongside a real weight/BMI value on a quick-weigh reading).

The same sheet also has a second table below the body-composition one: a `"Heart Rate"` section title row, its own header row (`Number, Date and Time, BPM`), then its data rows -- the scale's handgrip sensor apparently also records a heart rate at some weigh-ins. Discovered during implementation, not in the original sample inspection; the user confirmed it should be stored too (reusing `heart_rate`, the same metric_type Google Health-sourced readings already use).

## Goals / Non-Goals

**Goals:**
- Store every measurement the export contains, not just muscle mass (user's explicit choice, since the file is being parsed anyway).
- No new dependency: parse the `.xlsx` (a zip of XML) with `zipfile` + `xml.etree.ElementTree`, the same stdlib-first approach `glucose-pattern-views` used for percentiles instead of numpy.
- Reuse the existing `health_metrics` table and `insert_health_metrics` dedup exactly as `health-metrics-sync` already does -- this is just a second ingestion path into the same table.

**Non-Goals:**
- Supporting arbitrary `.xlsx` layouts -- this parses Wyze's specific "Body Composition Data" template only, the same way `libre.py`/`mytherapy.py` each parse one specific vendor format, not a general spreadsheet reader.
- Reconciling Wyze-sourced `weight`/`body_fat` readings against Google Health-sourced ones beyond what the existing dedup already does (see Decisions below) -- no merge/precedence logic between sources.
- Displaying the newly-stored-but-not-yet-shown fields (BMI, body water, lean body mass, bone mass, protein, visceral fat, BMR, metabolic age, skeletal muscle rate, fat content, subcutaneous fat) on the dashboard -- stored for a future change, per the user's own framing ("guarda todo, ya que estamos parseando el archivo").

## Decisions

**Parse with `zipfile` + `ElementTree`, not a new dependency.** An `.xlsx` is a zip archive; `xl/workbook.xml` lists sheets in order with their relationship ids, `xl/_rels/workbook.xml.rels` maps those to the actual `xl/worksheets/sheetN.xml` files, and each worksheet's `<row>`/`<c>` elements hold the cell data. This file's cells are all `t="inlineStr"` (text baked directly into the cell, no `sharedStrings.xml` lookup needed), which is what was found on manual inspection -- if a future export uses shared strings instead, that would need handling then, not preemptively guarded against here.

**Always ingest the first sheet, by document order in `workbook.xml`, never by matching the sheet's name.** The user's own sheet happened to be named after their Wyze account email in the sample file, but that's an account-specific string, not something to hardcode -- the Wyze app is understood to always list the logged-in account's own profile first, so position is the stable signal, not the name.

**Unit stripping and lb-to-kg conversion.** Every cell value is text with its unit suffix baked in (`"113.0kg"`, `"34.4%"`, `"1971"` unitless for BMR). Fields reported in lb (`Weight(lb)` -- skipped in favour of the kg column already present; `Muscle Mass`, `Lean Body Mass`, `Bone Mass`, `Fat Content`) are converted to kg (divide by 2.20462) so they're stored in the same unit as `weight`, consistent with how `health-metrics-sync` already stores `weight` in kg (converted from Google's grams).

**`"- -"` is "no reading", not zero or null-valued storage.** A quick weigh-in (foot contact too brief for bioimpedance) has a real weight/BMI but `"- -"` for every other field -- those fields are simply not included in that row's set of stored data points, not stored as `None`/0, matching the spec delta's explicit scenario.

**Metric-type naming**: `weight`, `bmi`, `body_fat`, `muscle_mass`, `muscle_mass_percent`, `body_water_percent`, `lean_body_mass`, `bone_mass`, `protein_percent`, `visceral_fat`, `bmr`, `metabolic_age`, `skeletal_muscle_rate_percent`, `fat_content`, `subcutaneous_fat_percent`. `weight` and `body_fat` intentionally reuse the exact metric_type strings `health-metrics-sync` already uses for the same Google Health-sourced measurements.

**Deliberately harmless overlap between Wyze-sourced and Google Health-sourced `weight`/`body_fat`.** The Wyze scale is the ultimate source for both paths (this file directly, or indirectly via Health Connect -> Google Health), so a given physical weigh-in may end up stored twice, once from each path, under slightly different timestamps (this export uses minute-precision `"2026.09.27 08:25 AM"`; Google Health's sync uses whatever precision Health Connect reports). `get_current_biometric_profile`'s existing "most recent value per metric type" query already handles this correctly without any change -- whichever path's reading has the latest `recorded_at` wins, which is the same behaviour it already has with multiple Google Health syncs over time. No reconciliation/precedence logic is added.

**`Number` (row sequence) and `Weight(lb)` columns are not stored.** `Number` is a row index, not a measurement; `Weight(lb)` is a unit-converted duplicate of `Weight(kg)`, which is stored directly without a conversion round-trip.

**The sheet is split into named sections (a title row with a single cell, e.g. `"Body Composition Data"` or `"Heart Rate"`), each with its own header row directly below it.** The parser detects any such title row generically (a row with exactly one non-empty cell), rather than hardcoding row numbers, since a future export with more or fewer body-composition rows would shift the `"Heart Rate"` section's row numbers. `Body Composition Data` is required for the file to be recognised at all; `Heart Rate` is optional -- an export from a scale model without a handgrip heart-rate sensor would have no such section, and that's not a reason to reject the whole file.

## Risks / Trade-offs

- **A future Wyze export format change (e.g. shared strings, a reordered/renamed column) would break this parser silently reporting "unrecognised file" rather than partially parsing** -- acceptable, matching how `libre.py`/`mytherapy.py` already fail closed on an unrecognised format rather than guessing.
- **Storing fields not yet displayed** (BMI, body water, etc.) is slightly more than the narrowest possible change, but was the user's own explicit choice weighed against re-parsing the same file again later for a future card.
