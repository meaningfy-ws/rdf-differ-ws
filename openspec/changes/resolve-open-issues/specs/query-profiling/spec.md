# query-profiling

Cites EPIC: resolve-open-issues. Issues: #134, #133, #135.

## ADDED Requirements

### Requirement: Timeout returns control immediately

`run_queries` SHALL stop waiting on a query once its timeout elapses, even if the
underlying SPARQL request thread is still blocked.

#### Scenario: A query hangs past the timeout

- **GIVEN** a query whose execution does not return within `timeout` seconds
- **WHEN** `run_queries` profiles it
- **THEN** it SHALL record status `TIMEOUT` for that query
- **AND** it SHALL proceed without waiting for the hung thread to finish

### Requirement: Fail fast when the triplestore is unreachable

The profiler `main()` SHALL verify the Fuseki endpoint is reachable before profiling.

#### Scenario: Endpoint down

- **GIVEN** the configured Fuseki endpoint is not reachable
- **WHEN** the profiler starts
- **THEN** it SHALL print a clear error and return a non-zero exit code
- **AND** it SHALL NOT execute any query

### Requirement: The profiling script is documented

The README SHALL describe the profiling script: its purpose, invocation, the key flags
(`--timeout`, `--csv-output`, `--create-delta-graphs`, `--endpoint`, `--dataset`), and exit
codes.

#### Scenario: README documents the profiler

- **WHEN** a user reads the README
- **THEN** they find the profiling script's purpose, invocation, flags and exit codes
- **AND** at least one concrete example command
