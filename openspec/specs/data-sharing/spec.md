# Data Sharing

## Purpose
Let the user generate a read-only view or export of the dashboard for a chosen date range, so he can share it with a doctor without giving the doctor access to celia itself.

Source of truth: `docs/PS-CELIA-001-Self-Hosted-Diabetes-Dashboard.md`, US-05.

## Requirements

### Requirement: Generate a scoped read-only share
The system SHALL produce a read-only view (link) or export (file) covering only the date range the user selects.

#### Scenario: User chooses to share a date range
- **WHEN** the user selects a date range and chooses to share
- **THEN** celia produces a read-only view (link) or export (file) covering only that range

### Requirement: Read-only access for share recipients
The system SHALL NOT allow anyone accessing a shared link to upload, sync, or edit data, and SHALL limit the view to the link's date range.

#### Scenario: Shared link is opened
- **WHEN** a generated read-only link is opened by anyone who has it
- **THEN** it shows the dashboard for that date range only, with no ability to upload, sync, or edit data

### Requirement: Revocable shares
The system SHALL allow the user to revoke a shared link so it no longer grants access.

#### Scenario: User revokes a share
- **WHEN** the user chooses to revoke a previously generated shared link
- **THEN** it no longer grants access
