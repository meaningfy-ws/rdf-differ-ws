# rest-api

Normative requirements for the RDF Differ REST API after migration to FastAPI (EPIC
`api-ui-fastapi-modernization`, DEC-1/DEC-7). The API SHALL preserve the existing contract — same
paths, verbs, and status codes — while changing only the entrypoint framework.

## ADDED Requirements

### Requirement: FastAPI-served REST API preserving the existing contract

The REST API SHALL be served by FastAPI and SHALL expose the same paths, HTTP verbs, and success
status codes as the prior Connexion implementation. The API SHALL publish a generated OpenAPI
document and interactive docs. Request and response bodies SHALL be defined by pydantic models, with
responses reusing the existing `api/domain/model.py` DTOs. Route functions SHALL call the existing
`services`/`adapters` unchanged and SHALL NOT contain business logic.

#### Scenario: List diffs

- **WHEN** a client sends `GET /diffs`
- **THEN** the API returns `200` with a JSON array of dataset descriptions

#### Scenario: OpenAPI is generated

- **WHEN** a client requests `GET /openapi.json`
- **THEN** the API returns `200` with an OpenAPI document describing every route
- **AND** interactive docs are served at `/docs`

#### Scenario: Routes are thin

- **WHEN** any route handles a request
- **THEN** it parses input, calls a service, and returns a model
- **AND** it contains no diff/report computation of its own

### Requirement: Multipart diff creation

The API SHALL accept `POST /diffs` as a multipart request carrying two uploaded RDF files
(`old_version_file_content`, `new_version_file_content`) plus form fields for dataset metadata, and
SHALL return `200` with the created task identifier and dataset name on success.

#### Scenario: Create a diff from two uploaded files

- **WHEN** a client posts two RDF files and valid dataset metadata to `POST /diffs`
- **THEN** the API enqueues the diff task
- **AND** returns `200` with the task id and dataset name

#### Scenario: Reject an unacceptable dataset name

- **WHEN** a client posts a dataset name containing characters outside `[A-Za-z0-9_:-]`
- **THEN** the API returns `409` and does not enqueue a task

### Requirement: Domain errors map to HTTP status codes

The API SHALL translate domain and not-found/conflict/validation conditions to the correct HTTP
status (`404`, `406`, `409`, `422`, `500`) via FastAPI exception handling, and SHALL return a
problem-style JSON body. Any unhandled exception SHALL produce `500` and SHALL be logged at `ERROR`
with a traceback.

#### Scenario: Unknown dataset is 404

- **WHEN** a client requests `GET /diffs/{id}` for a non-existent dataset
- **THEN** the API returns `404` with an explanatory JSON body

#### Scenario: Unhandled error is a logged 500

- **WHEN** a route raises an unexpected exception
- **THEN** the API returns `500` with a problem-style body
- **AND** an `ERROR`-level log line with a traceback is emitted
