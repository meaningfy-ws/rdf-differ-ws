# report-delivery

Cites EPIC: report-delivery-ux. Restores the report delivery loop (regression after 2.2.0).

## ADDED Requirements

### Requirement: Built reports can be viewed live

The UI SHALL serve a built report inline so the browser renders it — HTML as a page, JSON and
ASCII as readable text — without forcing a download.

#### Scenario: View an HTML report live

- **GIVEN** a dataset with a built `html` report for an application profile
- **WHEN** the user opens the report's **View** action
- **THEN** the UI SHALL respond with the report content and an inline content disposition
- **AND** the browser SHALL render the report as a page (not download it)

#### Scenario: View a report that does not exist

- **GIVEN** no report exists for the requested dataset/profile/type
- **WHEN** the user opens the View action
- **THEN** the UI SHALL show a clear message and redirect rather than error

### Requirement: The user is told when a report build completes

When a report build is triggered, the dataset view SHALL reflect that a build is in progress
and SHALL reveal the finished report without requiring a manual page refresh.

#### Scenario: Build then completion

- **GIVEN** the user triggers a report build on the dataset view
- **WHEN** the build task is still running
- **THEN** the view SHALL show a "building" indicator for that application profile and type
- **AND** when the task reaches a successful terminal state the view SHALL present the report as
  ready to view or download

#### Scenario: Build fails

- **GIVEN** a triggered report build whose task fails
- **WHEN** the dataset view detects the failed terminal state
- **THEN** it SHALL show an error indication instead of an indefinite "building" state

### Requirement: Built reports remain downloadable per variant

The dataset view SHALL list every built report grouped by application profile and template
type, each offering a download.

#### Scenario: Download a built report variant

- **GIVEN** a dataset with one or more built reports
- **WHEN** the user views the dataset
- **THEN** each built application-profile/template-type variant SHALL be listed with a download
  action that streams the report as an attachment

### Requirement: Inline report serving is sandboxed against stored XSS

Report content is derived from user-supplied RDF, so inline same-origin serving SHALL NOT
allow embedded scripts to execute. The view route SHALL pin the response media type from the
requested template type (never the upstream content-type) and SHALL sandbox the response.

#### Scenario: A hostile report cannot run scripts in the UI origin

- **GIVEN** a built report whose content contains markup or a misleading upstream content-type
- **WHEN** the user views it inline
- **THEN** the response SHALL carry a `Content-Security-Policy: sandbox` header and
  `X-Content-Type-Options: nosniff`
- **AND** the media type SHALL be derived from the template type (html→text/html, json→
  application/json, ascii→text/plain), not from the upstream response

### Requirement: Completion polling is bounded

The completion indicator SHALL poll a same-origin task-status endpoint at a fixed interval and
SHALL stop on a terminal state or after a bounded number of attempts.

#### Scenario: Task never resolves

- **GIVEN** a build whose task never reaches a terminal state
- **WHEN** the bounded number of poll attempts is exhausted
- **THEN** the view SHALL stop polling and prompt the user to refresh later
