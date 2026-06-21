# Capability: cli-diff-orchestration

Cites EPIC: resolve-open-issues. Issues: #132, #133.

## Requirement: Poll the task returned by the create call

The diff CLI (`infra/scripts/rdf-differ.sh`) SHALL wait on the Celery task id returned by
`POST /diffs` (the `uid` field), not on the first entry of `/tasks/active`.

### Scenario: create returns a uid
- **Given** the CLI runs the `diff` (or `full`) command with valid old/new files
- **When** `POST /diffs` responds with a JSON body containing `uid`
- **Then** the CLI SHALL poll `/tasks/{uid}` until terminal status
- **And** it SHALL NOT query `/tasks/active` to discover the task

### Scenario: create returns no uid
- **Given** `POST /diffs` responds without a usable `uid`
- **When** the CLI tries to determine which task to wait on
- **Then** it SHALL print a clear error and exit non-zero
- **And** it SHALL NOT fall back to waiting on an arbitrary active task

## Requirement: Fail fast when the API is unreachable

The CLI SHALL probe the API base URL once before issuing diff/report requests.

### Scenario: API down
- **Given** the API base URL is not reachable
- **When** the CLI starts a diff/report/full command
- **Then** it SHALL print a clear "API not reachable" message and exit non-zero
- **And** it SHALL NOT proceed to post a diff against a dead endpoint
