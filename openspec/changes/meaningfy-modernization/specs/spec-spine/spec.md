# spec-spine

## ADDED Requirements

### Requirement: Living specification spine
The repository SHALL carry an OpenSpec spine under `openspec/` — a `config.yaml`, the pinned
`meaningfy` schema, a `specs/` truth store and a `changes/` area — as the home for EPICs, PLANs
and normative specifications.

#### Scenario: Work is shaped as a change under the spine
- **WHEN** a new unit of work is shaped
- **THEN** it is authored as `openspec/changes/<id>/` containing `proposal.md` (EPIC),
  `design.md` and `tasks.md` (PLAN)

#### Scenario: The spine validates structurally
- **WHEN** `openspec validate --changes --strict` runs
- **THEN** each change exposes at least one `specs/<capability>/spec.md` delta and validation passes

### Requirement: Golden thread between artifacts
Each artifact SHALL cite its parent: the PLAN (`tasks.md`) cites its EPIC id on the first line.

#### Scenario: The PLAN cites its EPIC
- **WHEN** a `tasks.md` is authored
- **THEN** its first line references the EPIC the plan derives from
