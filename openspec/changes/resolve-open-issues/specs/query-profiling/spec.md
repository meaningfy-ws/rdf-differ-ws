# Capability: query-profiling

Cites EPIC: resolve-open-issues. Issues: #134, #133, #135.

## Requirement: Timeout returns control immediately

`run_queries` SHALL stop waiting on a query once its timeout elapses, even if the
underlying SPARQL request thread is still blocked.

### Scenario: a query hangs past the timeout
- **Given** a query whose execution does not return within `timeout` seconds
- **When** `run_queries` profiles it
- **Then** it SHALL record status `TIMEOUT` for that query
- **And** it SHALL proceed to the next query (or return) without waiting for the hung
  thread to finish

## Requirement: Fail fast when the triplestore is unreachable

The profiler `main()` SHALL verify the Fuseki endpoint is reachable before profiling.

### Scenario: endpoint down
- **Given** the configured Fuseki endpoint is not reachable
- **When** the profiler starts
- **Then** it SHALL print a clear error and return a non-zero exit code
- **And** it SHALL NOT execute any query

## Requirement: The profiling script is documented

The README SHALL describe the profiling script: its purpose, invocation, the key flags
(`--timeout`, `--csv-output`, `--create-delta-graphs`, `--endpoint`, `--dataset`), and exit
codes.
