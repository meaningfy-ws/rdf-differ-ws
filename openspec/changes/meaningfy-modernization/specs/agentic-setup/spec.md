# agentic-setup

## ADDED Requirements

### Requirement: CLAUDE-canonical agentic configuration
The repository SHALL keep `CLAUDE.md` as the single canonical agent-instruction file, with
`AGENTS.md` as a symlink to it (never a divergent copy).

#### Scenario: AGENTS.md resolves to CLAUDE.md
- **WHEN** an AGENTS.md-aware tool reads `AGENTS.md`
- **THEN** it reads the same content as `CLAUDE.md` because `AGENTS.md` is a symlink

### Requirement: Regenerable orientation index
The repository SHALL keep `.claude/memory/MEMORY.md` as a regenerable orientation index of at
most 200 lines; the durable truth is `openspec/specs/`.

#### Scenario: Index disagrees with the specs
- **WHEN** `.claude/memory/MEMORY.md` conflicts with `openspec/specs/`
- **THEN** `openspec/specs/` is authoritative
