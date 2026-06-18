<!-- Regenerable orientation INDEX for RDF Differ. Auto-loaded into every session (first ~200
     lines) — keep it ≤200 lines and curate ruthlessly. This is an INDEX, NOT authority: the truth
     is openspec/specs/ (durable capability specs) and openspec/config.yaml's `context:` field. If
     this note ever disagrees with openspec/specs/, specs/ wins. Stable, CONFIRMED facts only. -->

# Project Memory (index) — RDF Differ

## Project Overview

- Diffs two versions of an RDF dataset and reports the changes (SKOS/OWL aware); exposed as a
  Flask/Connexion REST API + Flask UI + Celery worker + Click CLI.
- Top-level package: `rdf_differ/` (no `/src`). Default branch: `master`.
- Layers: `entrypoints → services → domain`, `adapters → domain`. Enforced by `.importlinter`
  (`make check-architecture`). Legacy `rdf_differ/utils/` pending redistribution.
- Tooling (migrating): Poetry, Ruff, mypy, pytest + pytest-bdd, import-linter. `make` is the
  dev/CI interface (`make help`).

## Spine (where work and truth live)

- EPIC ≡ `openspec/changes/<id>/proposal.md`; PLAN ≡ `design.md` + `tasks.md`.
- Durable truth: `openspec/specs/`. Orientation: `openspec/config.yaml: context:`.
- Drive with `/opsx:*` (propose, explore, apply, sync, archive). Golden thread: cite your parent.

## Reference

- `openspec/changes/meaningfy-modernization/` — the active modernization EPIC + PLAN (slice-per-commit).
- GitNexus skills under `.claude/skills/gitnexus/` (impact/explore/refactor); MCP via `.mcp.json`.

## Key Decisions

- 2026-06-18: Modernize to the Meaningfy standard as a separate branch/PR (`feature/meaningfy-modernization`),
  keeping `domain/` (no rename to `models/`), Python floor 3.12. The `load_versions.sh → Python` rewrite
  is parked on `feature/rewrite-load-versions-to-python` (separate PR). (See the modernization EPIC.)

## Gotchas

- External datastores: Jena Fuseki (SPARQL) + Redis (Celery broker/results). Tests may assume them.
- `.gitnexus/` (≈112 MB) and `.claude/settings.local.json` are git-ignored — never commit them.
