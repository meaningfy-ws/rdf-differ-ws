# web-ui

Normative requirements for the RDF Differ web UI after rebuild on FastAPI + Jinja2 + modern CSS
(EPIC `api-ui-fastapi-modernization`, DEC-2/DEC-3). The UI SHALL preserve the existing pages and
journeys while replacing Flask and hardening the API client.

## ADDED Requirements

### Requirement: FastAPI + Jinja2 server-rendered UI

The UI SHALL be served by FastAPI rendering Jinja2 templates, exposing the existing pages — home
(dataset list), create-diff, view-dataset (with build-report), report download, active-tasks (with
revoke). It SHALL NOT depend on Flask or Flask-WTF. Form input SHALL be validated by pydantic models;
invalid input SHALL re-render the form with messages rather than error.

#### Scenario: Home lists datasets

- **WHEN** a user opens `/`
- **THEN** the UI renders the list of available dataset diffs

#### Scenario: Create-diff validates input

- **WHEN** a user submits the create-diff form with a missing required field
- **THEN** the UI re-renders the form with a validation message
- **AND** does not call the API

### Requirement: Resilient API client

The UI SHALL call the REST API through an `httpx`-based client configured with explicit timeouts. The
client SHALL NOT parse a response body as JSON without guarding for non-JSON/error responses; an API
error or timeout SHALL surface to the user as a flash message and SHALL NOT cause a UI `500`.

#### Scenario: API error becomes a flash, not a crash

- **WHEN** the API returns a non-2xx, non-JSON response during a UI action
- **THEN** the UI shows an error flash message
- **AND** the UI page still renders with status `200`

#### Scenario: API timeout is handled

- **WHEN** an upstream API call exceeds the configured timeout
- **THEN** the UI shows an error flash message and renders normally

### Requirement: Modern, responsive styling

The UI SHALL ship a single coherent CSS design system (layout, typography, forms, tables, cards,
navigation, flash messages) applied across all pages, and SHALL render usably on narrow (mobile) and
wide (desktop) viewports.

#### Scenario: Pages share one design system

- **WHEN** a user navigates between any two UI pages
- **THEN** both render with the shared stylesheet (consistent nav, typography, components)
