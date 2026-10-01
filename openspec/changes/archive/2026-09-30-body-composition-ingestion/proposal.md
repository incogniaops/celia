# Proposal

## Why

The user wants an estimated A1C (the GMI already computed by `glucose-pattern-views`) and muscle mass shown alongside the existing biometric cards (weight, body fat, heart rate, resting heart rate). Muscle mass isn't one of the six data types `health-metrics-sync` gets from the Google Health API — it, and a good deal of other body-composition data (BMI, body water, lean body mass, bone mass, protein, visceral fat, BMR, metabolic age, skeletal muscle rate, fat content, subcutaneous fat), only exists in the Wyze scale's own export, which the user has uploaded as a real sample (`data/wyze/scaledata_300926.xlsx`).

## What Changes

- Parse an uploaded Wyze "Body Composition Data" `.xlsx` export and store every measurement it contains as a `health_metrics` row (reusing the existing table and its (metric_type, recorded_at) deduplication) -- not just muscle mass, since the file is being parsed anyway (user's explicit choice).
- The export's first sheet is always the logged-in account's own data; any additional sheet (in the user's sample, a second profile sharing the same scale) is a different person's data and is never ingested.
- Add muscle mass to the dashboard's biometric-profile cards, alongside weight, body fat, heart rate and resting heart rate.
- Move the estimated A1C (GMI) next to those same cards, as its own "A1C (estimated)" card, rather than only as text inside the time-in-range summary further down the page.

## Capabilities

### New Capabilities
- `body-composition-ingestion`: parse a Wyze body-composition `.xlsx` export and store its measurements.

### Modified Capabilities
- `dashboard`: the biometric-profile cards gain muscle mass and an estimated-A1C card; the time-in-range summary keeps average glucose and %CV but no longer repeats GMI, since it now has a dedicated card.

## Impact

- **Changed code**: `app/parsers/wyze.py` (new), `app/routers/uploads.py` (new `/uploads/wyze` endpoint), `app/templates/upload_wyze.html` and `upload_wyze_result.html` (new, mirroring the Libre/MyTherapy upload forms), `app/templates/dashboard_empty.html` (mention the new upload option), `app/dashboard_data.py` (add `muscle_mass` to `BIOMETRIC_METRIC_TYPES`), `app/templates/dashboard_content.html` (A1C card, time-in-range text tweak).
- **No database schema changes** -- reuses the existing `health_metrics` table and `insert_health_metrics`.
- **No new dependency**: `.xlsx` is a zip of XML; parsed with the standard library (`zipfile` + `xml.etree.ElementTree`), the same "stdlib where feasible" approach `glucose-pattern-views` took for percentiles.
- **Only the fields with a real reading are stored**: the Wyze app's own export marks bioimpedance-only fields (everything except weight/BMI) as `"- -"` on a quick-weigh reading that didn't make foot contact long enough -- these are not stored as zero or null-valued rows, they're simply absent for that timestamp.
