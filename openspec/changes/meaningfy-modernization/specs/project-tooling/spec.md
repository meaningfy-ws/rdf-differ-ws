# project-tooling

## ADDED Requirements

### Requirement: Standardised toolchain through make targets
The project SHALL expose its install, lint, type-check, architecture-check and test
operations through `make` targets, so contributors and CI invoke a single interface.

#### Scenario: Quality gate runs lint and architecture checks
- **WHEN** a contributor runs `make check-quality`
- **THEN** Ruff linting and the import-linter architecture contracts run
- **AND** the command fails if either reports a violation

#### Scenario: Dependencies install via Poetry
- **WHEN** a contributor runs `make install`
- **THEN** Poetry installs the declared dependency groups from the lockfile

### Requirement: Enforced architecture boundaries
The codebase SHALL enforce the cosmic-python layer direction
`entrypoints > services > adapters > domain > utils` via import-linter contracts.

#### Scenario: A lower layer importing a higher layer fails the gate
- **WHEN** a module in `adapters` imports from `services`
- **THEN** `make check-architecture` fails with a broken-contract error

### Requirement: Python baseline and coverage gate
The project SHALL target Python 3.12 or newer and SHALL measure test coverage with a
non-regression gate.

#### Scenario: Coverage below the configured floor fails the suite
- **WHEN** `make test` runs and total coverage is below the configured `fail_under`
- **THEN** the test command exits non-zero
