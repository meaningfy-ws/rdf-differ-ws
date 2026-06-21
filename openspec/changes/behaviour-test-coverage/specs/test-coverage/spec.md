# test-coverage

Normative requirements for the project-wide behaviour-test suite (EPIC `behaviour-test-coverage`).
These constrain the *test suite*, not production behaviour.

## ADDED Requirements

### Requirement: Behaviour coverage for every main capability

The suite SHALL provide Gherkin features with executable pytest-bdd step definitions for each main
capability — RDF loading & diff computation, reporting, the REST API, the web UI, and the CLI — and
each feature SHALL include at least one happy-path, one edge-case, and one negative-path scenario.

#### Scenario: Each capability has a behaviour feature

- **WHEN** the test suite is collected
- **THEN** a feature file exists for loading/diff, reporting, the REST API, the web UI, and the CLI
- **AND** each contains happy-path, edge-case, and negative-path scenarios

### Requirement: Default run needs no infrastructure

The behaviour suite SHALL run to green without any running Fuseki, Redis, or Celery, except scenarios
explicitly tagged `@integration`, which SHALL be excluded from the default run.

#### Scenario: Infra-free features pass without services

- **WHEN** the behaviour features run with no services started
- **THEN** every non-`@integration` scenario passes
- **AND** `@integration` scenarios are deselected

### Requirement: Reuse existing data and profiles

The suite SHALL exercise behaviour using the existing `tests/test_data/` fixtures and the bundled
application profiles, and SHALL NOT commit new heavyweight test data.

#### Scenario: Loading uses existing sample data

- **WHEN** a loading/diff scenario runs
- **THEN** it loads versions from files already present under `tests/test_data/`
