<!-- meaningfy-template-version: 3.0.0 -->
<!-- CANONICAL agent instruction file (Claude Code loads CLAUDE.md). AGENTS.md is an OPTIONAL
     SYMLINK to this file (ln -s CLAUDE.md AGENTS.md) for AGENTS.md-aware tools. Edit THIS file
     only — never edit AGENTS.md directly (CLAUDE-canonical; DEC-4). This repo CLAUDE.md is the
     repo operating manual: it ROUTES to skills and to the global ~/.claude/CLAUDE.md standard;
     it never restates that standard (DEC-12 — global vs repo split).
     The gitnexus block at the very bottom is auto-managed between its markers — do not hand-edit it. -->

# Project: RDF Differ

Meaningfy project. Build clean, layered, well-tested code; minimise WTFs-per-minute. The
company-wide standard lives in the **global `~/.claude/CLAUDE.md`** (Clean Code, Clean
Architecture, testing, tooling) — this file does **not** repeat it; it ROUTES to it and to the
installed skills, and records only what is specific to **this** repo.

## Skill routing (use the skill for the task)

- Structuring Python code (domain/adapters/services/entrypoints, SOLID, CI) → **cosmic-python**
- Keeping code minimal — YAGNI, avoid over-engineering, simplest working approach → **ponytail**
  (`/ponytail` to set intensity; `/ponytail-review` for a delete-list on the diff)
- System / solution design (C4, ADRs, contracts) → **architecture**
- Modelling the domain / generating code from a model (`make generate-models`) → **conceptual-modelling**
- Any new feature or non-trivial change → start by exploring options (**superpowers:brainstorming**)
- Any feature or bugfix implementation → **superpowers:test-driven-development** (tests first)
- Debugging → **superpowers:systematic-debugging**
- Shaping an EPIC + deriving its PLAN → **epic-planning** + the **`/opsx:*`** workflow commands
- Spec readiness (the PLAN clarity gate, ≥9/10) → **clarity-gate**
- BDD features → **bdd-gherkin**
- Commits / branches / PRs → **meaningfy-git-workflow** (mechanics via **commit-commands**)
- Pre-PR review → **meaningfy-code-review** (+ external **code-review**)
- Deploy / release / versioned image → **ci-cd-delivery**
- Docs → **technical-writing**

If a request conflicts with these, flag it before proceeding.

## The spine — where work is shaped and remembered

This repo carries the Meaningfy **spine** under `openspec/` (OpenSpec, schema `meaningfy`):

- **EPIC ≡ `openspec/changes/<id>/proposal.md`** (the Shape-Up work shape: appetite, why, solution,
  key decisions, rabbit-holes, no-gos).
- **PLAN ≡ `openspec/changes/<id>/design.md` + `tasks.md`** (the clarity gate scores the pair ≥9/10).
- **Normative requirements ≡ `openspec/changes/<id>/specs/<cap>/spec.md`** (RFC-2119 SHALL +
  Given/When/Then; no EARS). They merge into **`openspec/specs/`** — the durable truth — on archive.
- **Seed inputs** (briefs, notes) live in `openspec/changes/<id>/inputs/` — preserved, never groomed.
- **Orientation** is `openspec/config.yaml`'s `context:` field (the native index) — **not** a
  hand-curated MEMORY.md. The truth is `openspec/specs/`.

Drive it with the `/opsx:*` commands (`propose`, `explore`, `apply`, `sync`, `archive` — core profile).

**External method skills land in the spine (binding).** `superpowers` provides *disciplines*, not a
parallel spec system — its artifacts MUST land in `openspec/changes/<id>/`, never a `docs/superpowers/`
tree. A **brainstorming** design feeds the **EPIC** (`proposal.md`); **writing-plans is SUPERSEDED** by
the **PLAN** (`design.md`+`tasks.md`); execution uses superpowers TDD, tracked via `/opsx:apply`.

**Golden thread (cite your parent).** Each artifact cites the one above it: the PLAN (`tasks.md`)
cites its EPIC id on the first line; specs cite their capability; commits reference the change. This
is how any commit traces up to the requirement that justifies it.

## Implementation loop (orchestration)

Before editing a symbol, run gitnexus impact (status → analyze → impact/context); stop and
report HIGH/CRITICAL risk. Loop: generate (tests first) → verify (run tests) → integrate
(present, get consent). On a design-level failure, fix the spec, not the code (Rule of
Divergence). Commit only on explicit developer consent.

## Working conventions

- The innermost layer is **`domain`** (the book's `models/`). Direction:
  `entrypoints → services → domain`, `adapters → domain`. `domain` imports nothing upward.
  Enforced by `.importlinter`; checked via `make check-architecture`.
- Run Python tooling through Poetry (`poetry run pytest`, `poetry run ruff`, …). Never invoke
  bare `python`/`pytest` — prefer the `make` targets.
- Default branch is **`master`** (the PR target). Branch off it; never commit to it directly.

## `.claude/` is a regenerable index — the truth is `openspec/specs/`

`.claude/memory/MEMORY.md` is a cheap orientation note (≤200 lines; stable patterns only). It is an
**index, not authority** — if it disagrees with `openspec/specs/`, `specs/` wins. The legacy
`.claude/memory/epics/EPIC.md`+`PLAN.md`+`task.md` model is **superseded** by the spine's native
artifacts above; do not reintroduce parallel epic files under `.claude/`.

## Project specifics

- **Archetype:** product (deployable) — a Flask/Connexion REST API + Flask UI + Celery worker + Click CLI.
- **Top-level package:** `rdf_differ/` (no `/src`).
- **Layers / modules:** single component — `rdf_differ/{domain,adapters,services,entrypoints}` plus a
  legacy `rdf_differ/utils/` (TODO: redistribute into the right layers — see the modernization change).
- **Domain model:** hand-written in `rdf_differ/domain/model.py`. A LinkML `model/` + `make generate-models`
  seam is planned (modernization DEC-6); no code generation yet.
- **Datastores / external systems:** an RDF triplestore over SPARQL (Jena Fuseki; `SPARQLWrapper`/`rdflib`),
  Redis (Celery broker + result backend), Celery worker + Flower; `eds4jinja2` for report rendering.
- **Deployable?** yes — Docker (image/compose under `docker/`, moving to `infra/`). CD pipeline is a
  TODO stub pending DevOps ratification (modernization DEC-7).
- **Make targets:** `make` is the dev/CI interface (`make help`). The toolchain is being migrated to
  Poetry + Ruff + mypy + `check-all` across the modernization slices.
- **GitNexus repo name:** `rdf-differ`.

> **Active modernization.** This repo is mid-migration to the Meaningfy standard, shaped as
> `openspec/changes/meaningfy-modernization/` (EPIC + PLAN, applied slice-per-commit). The parked
> `load_versions.sh → Python` rewrite lives on `feature/rewrite-load-versions-to-python` (separate PR).

See `docs/` for project documentation.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **rdf-differ** (4056 symbols, 4712 relationships, 42 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "master"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/rdf-differ/context` | Codebase overview, check index freshness |
| `gitnexus://repo/rdf-differ/clusters` | All functional areas |
| `gitnexus://repo/rdf-differ/processes` | All execution flows |
| `gitnexus://repo/rdf-differ/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
