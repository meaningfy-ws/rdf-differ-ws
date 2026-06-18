# Gap analysis — rdf-differ vs Meaningfy standard (seed input, not groomed)

Captured 2026-06-18 at the start of the modernization. Source: `scaffold.sh --dry-run` (mechanical
file-presence) + the brownfield rubric (dimensions a file check cannot see). Base ref: `master`.

Archetype: **product** (Flask API + Connexion + Flask UI + Celery worker + Click CLI), **deployable**.

| Dimension | Status | Findings (against `master`) |
|---|---|---|
| Layout | ✅ good | `rdf_differ/` top-level, no `/src`. Layers `domain/ adapters/ services/ entrypoints/` + non-layer `utils/`. |
| pyproject | ❌ missing | No `pyproject.toml`. Deps via `setup.cfg` + `requirements/{common,dev,prod}.txt`. No Poetry. |
| Tool configs | ❌ missing | No `ruff.toml`, `mypy.ini`, `pytest.ini`, `.coveragerc`, `.importlinter`, `.pre-commit-config`, `sonar-project.properties`. Pytest config in `setup.cfg`. |
| Lint/format | ⚠️ legacy | `flake8` only. No Ruff, no mypy. |
| Tests | ⚠️ partial | pytest + pytest-bdd present. `tests/unit + features + steps`. Missing type-split tree (unit/feature/e2e/integration), marker-injection conftest, enforced `--cov-fail-under=80`. Committed test artifacts (junit/cucumber/.coverage). |
| Architecture | ❌ unenforced | No `.importlinter`. Layer direction by convention only. |
| Agent file | ⚠️/n.a. on master | On `master`: no CLAUDE.md/AGENTS.md/.mcp.json/.claude/skills at all. (They exist only on the load_versions branch; DEC-4 wants canonical CLAUDE.md + AGENTS.md symlink.) |
| Spine | ❌ missing | No `openspec/`. No `/opsx:*`. (Projected by this change.) |
| Memory | ⚠️ partial | `.claude/` has only `settings.local.json` on master. No repo `.claude/memory/MEMORY.md` index. |
| Domain model | ❌ missing | Product archetype expects `model/` (LinkML) + `make generate-models`. None present. |
| Docs | ⚠️ legacy | `docs/` is Sphinx (`conf.py`, `index.rst`, myst), not Antora/Diátaxis. |
| Infra | ⚠️ legacy | `docker/` at top level, not `infra/`. |
| CI | ⚠️ legacy | `.github/workflows/{test,package}.yml` inline, Python 3.8, not calling `make` targets mirroring `check-all`. |
| Versions | ❌ outdated | Python **3.8** (EOL). No `requires-python` bound. Deps pinned to 2021-era ranges. |

Mechanical gap count (`scaffold.sh --dry-run`): ~45 files to create, ~12 to keep.

## Decisions taken during intake
- Scope: **Full conformance** + Python 3.12 minimum + dependency bumps.
- Sequencing: the in-flight `load_versions.sh → Python` rewrite is **parked** (branch
  `feature/rewrite-load-versions-to-python`, 5 commits, stash holding floating agentic files).
  Modernization is a **separate branch/PR** off `master`. Two PRs total.
- Process: shaped as this OpenSpec change (EPIC + PLAN), clarity-gated ≥9/10, applied in slices.
- Branch hygiene: 9 stale fully-merged branches dropped; only `master` + parked load_versions remain.

## Open question carried into design
- The spine `config.yaml` blesses `domain` as the innermost layer name, while the global Meaningfy
  prompt says `models/`. Keeping `domain/` is lower-risk and spine-consistent — see design.md.
