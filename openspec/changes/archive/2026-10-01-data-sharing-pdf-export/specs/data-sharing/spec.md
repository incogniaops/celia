# Spec Delta

## MODIFIED Requirements

### Requirement: Generate a scoped read-only share
The system SHALL produce a downloadable PDF export covering only the date range the user currently has selected, typeset as an editorial clinical report so the user can print it or send it to a doctor by email himself. The report's layout is modelled on the user's own FreeStyle Libre/LibreView AGP report: a header identifying the user and the covered date range, a time-in-range summary (percentage of readings in each glucose band, against the same targets the dashboard already uses), a glucose-statistics summary (average glucose, estimated A1C/GMI, glucose variability), an ambulatory glucose profile (percentile-band) chart, and a daily-glucose-profile grid (one small profile per calendar day in the range).

#### Scenario: User chooses to share a date range
- **WHEN** the user selects a date range and chooses to share
- **THEN** celia generates a downloadable PDF covering only that date range, available for immediate download

#### Scenario: Exported PDF's content matches the dashboard's own figures
- **WHEN** a PDF is generated for a date range that also has glucose data on the dashboard
- **THEN** the PDF's time-in-range percentages, average glucose, estimated A1C/GMI and glucose-variability figures match the dashboard's own figures for the same range exactly

#### Scenario: No glucose data in the selected range
- **WHEN** the user requests a PDF export for a date range with no glucose readings
- **THEN** celia still generates a PDF identifying the user and the requested range, showing the absence of data rather than a 0%-everywhere or blank report

#### Scenario: Birth date and real age are never shown
- **WHEN** a PDF is generated
- **THEN** it does not show the user's birth date or chronological age anywhere, even though the real Abbott/LibreView report it is modelled on does -- matching the dashboard's existing rule of never revealing the user's real age

#### Scenario: Sensor time-active is not claimed
- **WHEN** a PDF is generated
- **THEN** it does not show a "percentage of sensor time active" figure, since celia has no sensor-log data to compute one from in this iteration

#### Scenario: No automated clinical pattern commentary
- **WHEN** a PDF is generated
- **THEN** it does not include any automatically-generated clinical commentary or pattern-detection statement (e.g. "no adverse glucose patterns detected") -- celia presents the same computed figures and charts the dashboard already shows, and leaves interpretation to the doctor

## REMOVED Requirements

### Requirement: Read-only access for share recipients
**Reason**: This requirement describes access control for a shared *link* (view-only web access for anyone who has it). This iteration resolves OD-02 as a downloadable PDF export instead -- there is no link, so there is nothing for a recipient to "access" beyond opening a file the user chose to send them.
**Migration**: None needed. If a share-link mechanism is proposed in a future iteration, its own access-control requirement should be specified fresh rather than reusing this one, since a link's access model and a PDF's are not the same shape.

### Requirement: Revocable shares
**Reason**: Revocation only makes sense for a live, re-checkable share mechanism (a link). A downloaded PDF cannot be revoked once the user has sent or printed it, the same way LibreView's own AGP report PDF can't be "unshared" after being emailed.
**Migration**: None needed. If a share-link mechanism is proposed in a future iteration, re-specify revocation for that mechanism directly.
