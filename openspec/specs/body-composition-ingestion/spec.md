# Body Composition Ingestion

## Purpose
Ingest the user's Wyze scale body-composition export (`.xlsx`) -- muscle mass, BMI, body water, lean body mass, bone mass, protein, visceral fat, BMR, metabolic age, skeletal muscle rate, fat content and subcutaneous fat -- none of which the Google Health API provides, so these are visible alongside the other biometric data without manual data entry.

## Requirements

### Requirement: Ingest a Wyze body-composition export
The system SHALL parse an uploaded Wyze "Body Composition Data" `.xlsx` export and store every measurement present in each row (weight, BMI, body fat, muscle mass, muscle mass %, body water %, lean body mass, bone mass, protein %, visceral fat, BMR, metabolic age, skeletal muscle rate %, fat content, subcutaneous fat %) as its own `health_metrics` data point, with its original date and time.

#### Scenario: A full bioimpedance reading is uploaded
- **WHEN** a row in the export has every measurement present
- **THEN** celia stores each measurement as its own health-metrics data point for that timestamp

#### Scenario: A quick-weigh reading only has weight and BMI
- **WHEN** a row in the export marks the bioimpedance-only fields as `"- -"` (no foot contact reading)
- **THEN** celia stores only weight and BMI for that timestamp, not a zero or null-valued row for the missing fields

### Requirement: Ingest the optional Heart Rate section
The system SHALL parse the export's optional "Heart Rate" section (title row, header row `Number, Date and Time, BPM`, data rows), when present, storing each reading as a `heart_rate` health-metrics data point, the same metric_type Google Health-sourced heart-rate readings use.

#### Scenario: The export includes a Heart Rate section
- **WHEN** the uploaded export has a "Heart Rate" section below the body-composition data
- **THEN** celia stores each of its readings as a `heart_rate` data point

#### Scenario: The export has no Heart Rate section
- **WHEN** the uploaded export has no "Heart Rate" section (e.g. a scale model without a handgrip sensor)
- **THEN** celia still ingests the body-composition data normally, without treating the missing section as an error

### Requirement: Only the account's own sheet is ingested
The system SHALL only ingest the first sheet of a Wyze export, which is always the logged-in account's own data; it SHALL NOT ingest any additional sheet.

#### Scenario: The export contains more than one profile's data
- **WHEN** the uploaded export has more than one sheet (for example, a second person sharing the same scale)
- **THEN** celia only stores the first sheet's rows, and does not store any other sheet's data

### Requirement: Reject unrecognised files
The system SHALL reject an uploaded file that does not match the expected Wyze body-composition `.xlsx` format.

#### Scenario: Unrecognised file uploaded
- **WHEN** the user uploads a file that does not match the expected Wyze export format
- **THEN** the upload is rejected and the user is told the file could not be recognised

### Requirement: No duplicate data points on overlapping re-uploads
The system SHALL NOT create duplicate health-metrics rows when an uploaded export overlaps a period already ingested, consistent with how Google Health-sourced metrics are deduplicated.

#### Scenario: Overlapping export re-uploaded
- **WHEN** the user re-uploads a Wyze export that overlaps readings already ingested
- **THEN** celia does not create duplicate rows for the overlapping timestamps
