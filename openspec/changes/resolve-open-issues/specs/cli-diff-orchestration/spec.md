# cli-diff-orchestration

Cites EPIC: resolve-open-issues. Issues: #132, #133.

## ADDED Requirements

### Requirement: Poll the task returned by the create call

The diff CLI (`infra/scripts/rdf-differ.sh`) SHALL wait on the Celery task id returned by
`POST /diffs` (the `uid` field), not on the first entry of `/tasks/active`.

#### Scenario: Create returns a uid

- **GIVEN** the CLI runs the `diff` (or `full`) command with valid old/new files
- **WHEN** `POST /diffs` responds with a JSON body containing `uid`
- **THEN** the CLI SHALL poll `/tasks/{uid}` until terminal status
- **AND** it SHALL NOT query `/tasks/active` to discover the task

#### Scenario: Create returns no uid

- **GIVEN** `POST /diffs` responds without a usable `uid`
- **WHEN** the CLI tries to determine which task to wait on
- **THEN** it SHALL print a clear error and exit non-zero
- **AND** it SHALL NOT fall back to waiting on an arbitrary active task

### Requirement: Fail fast when the API is unreachable

The CLI SHALL probe the API base URL once before issuing diff/report requests.

#### Scenario: API down

- **GIVEN** the API base URL is not reachable
- **WHEN** the CLI starts a diff/report/full command
- **THEN** it SHALL print a clear "API not reachable" message and exit non-zero
- **AND** it SHALL NOT proceed to post a diff against a dead endpoint
