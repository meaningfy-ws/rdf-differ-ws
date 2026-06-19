# observability

Normative requirements for request/response logging across the API and UI (EPIC
`api-ui-fastapi-modernization`, DEC-8). Logging SHALL be sufficient to debug a request without a
local repro, and SHALL live only in the entrypoint/service layers.

## ADDED Requirements

### Requirement: Status-class request logging

Both the API and the UI SHALL log every handled request at a level chosen by its response status
class: **2xx and 3xx at `INFO`**, **4xx at `WARNING`**, and **5xx at `ERROR` with a traceback**. Each
log line SHALL include the HTTP method, path, status code, and latency, plus the dataset or task
identifier when present in the request. Logging SHALL be implemented as entrypoint middleware (and the
UI's API-client wrapper) and SHALL NOT be placed in `domain` or `adapters`.

#### Scenario: Successful request logs at INFO

- **WHEN** a request completes with a `200`
- **THEN** an `INFO` log line is emitted with method, path, `200`, and latency

#### Scenario: Client error logs at WARNING

- **WHEN** a request completes with a `404`
- **THEN** a `WARNING` log line is emitted with method, path, and `404`

#### Scenario: Server error logs at ERROR with traceback

- **WHEN** a request completes with a `500`
- **THEN** an `ERROR` log line with a traceback is emitted, including method, path, and `500`

### Requirement: Upstream call logging from the UI

The UI SHALL log each call it makes to the REST API using the same status-class levels, so that an API
failure observed by the UI is traceable from the UI logs alone.

#### Scenario: UI logs a failing upstream call

- **WHEN** the UI's API client receives a `500` from the API
- **THEN** the UI emits an `ERROR` log line identifying the upstream method, path, and status
