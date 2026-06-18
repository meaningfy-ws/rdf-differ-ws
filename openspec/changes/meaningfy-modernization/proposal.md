# EPIC: Bring rdf-differ up to the Meaningfy standard

## Appetite

**Large.** This is a multi-slice migration project, not a single fix. The budget is fixed: land it in
independently reviewable, always-green slices (one concern per commit/PR). If a slice overruns its
risk budget (notably the docs port and the dependency bump), it is deferred — not forced.

## Why

`rdf-differ` is a healthy but 2021-era Flask codebase: Python 3.8 (EOL), no `pyproject.toml`, no
enforced architecture, no spec spine, Sphinx docs, and CI that inlines commands. It predates the
current Meaningfy standard on tooling, the OpenSpec spine, and CI. We are about to do real feature
work on it (the parked `load_versions.sh → Python` rewrite); modernizing **first** means that work —
and everything after — lands under enforced layering, tests, and the spec spine instead of widening
the gap.

## Solution outline

Apply the brownfield method from `project-setup`: **audit → shape (this change) → approve → apply in
safe slices, least-risk first**, each slice gated behind `make check-all`. The ordering moves from
zero-risk additive files outward to the high-blast-radius moves:

1. Additive standalone configs (Ruff, mypy, pytest, coverage, import-linter, pre-commit, sonar).
2. The OpenSpec spine (this change projects it).
3. Agentic files — canonical `CLAUDE.md` + `AGENTS.md` symlink, `.claude/memory` index.
4. `pyproject.toml` / Poetry migration (deps from `requirements/*` + `setup.cfg`).
5. Tooling swap — Ruff/mypy replace flake8; fix surfaced debt in dedicated commits.
6. **Python 3.8 → 3.12 + dependency bumps** (Flask/Connexion/Celery/rdflib/SPARQLWrapper etc.).
7. Test tree reorg — type-split dirs, marker-injection conftest, coverage gate ≥80%.
8. `.importlinter` hardened from permissive to real per-layer contracts.
9. Pillars — Antora docs (port from Sphinx), `docker/ → infra/`, conditional `model/` (LinkML).

## Key decisions

- **DEC-1**: Modernize on a dedicated branch off `master`, separate from the parked `load_versions`
  work — **two PRs**. Rationale: keep history clean; modernization must not entangle feature work.
- **DEC-2**: **Keep `domain/` as the innermost layer name** (do *not* rename to `models/`). Rationale:
  the spine `config.yaml` itself blesses `domain`; renaming touches every import for zero functional
  gain. Lowest-risk, spine-consistent.
- **DEC-3**: Python **3.12** as the floor (`requires-python = ">=3.12"`); bump dependencies to current
  majors in the same slice they require, behind the test suite.
- **DEC-4**: `CLAUDE.md` is canonical; `AGENTS.md` is a symlink to it (Meaningfy DEC-4). Carry over the
  useful gitnexus skills/index; do not resurrect the parked floating copies.
- **DEC-5**: Adopt the canonical stack — Poetry, Ruff, mypy, pytest+pytest-bdd, coverage.py,
  import-linter, OpenSpec spine, Antora, Makefile — deviating only with a stated reason.
- **DEC-6**: `model/` (LinkML) + `make generate-models` is scaffolded as a **seam** (the domain model
  is currently hand-written in `rdf_differ/domain/model.py`); actually generating from LinkML is a
  follow-up, not part of this change.
- **DEC-7**: The CD half of CI (`deploy.yaml`) lands as a clearly-marked **TODO stub** until DevOps
  ratifies the deployment contract; only `ci.yaml` + `docs.yaml` are wired live.

## Rabbit-holes

- **The dependency bump.** Flask 2.2 → 3.x, Connexion 2 → 3, Celery, rdflib 7, SPARQLWrapper — these
  have breaking API changes. Time-box; if a single dep's migration blows the budget, pin it and file
  a follow-up rather than rewriting call sites under pressure.
- **Sphinx → Antora.** Port the *information architecture* (Diátaxis) and the essential content; do
  **not** hand-migrate every legacy page 1:1. The big `README.md` and `db/` report samples stay.
- **`utils/` placement.** Resist a deep re-layering of `rdf_differ/utils/` — relocate into the right
  layer/commons only where import-linter forces it; otherwise leave it.

## No-gos

- **No behaviour changes.** This is structure/tooling/version only. No new features, no API changes,
  no diffing-logic changes. The `load_versions` rewrite stays parked and is out of scope.
- **No big-bang.** Never mix the high-blast-radius moves (dep bump, test reorg) with other concerns
  in one commit. No slice merges on a red `make check-all`.
- **No `/src` layout** (already top-level — keep it), no rename of `domain/` (DEC-2), no LinkML code
  generation in this change (DEC-6), no live deploy pipeline (DEC-7).
- **No deletion of the parked branch** or its committed `load_versions` spec work.

---

## What Changes

- **Add** root tool configs: `pyproject.toml` (Poetry), `ruff.toml`, `mypy.ini`, `pytest.ini`,
  `.coveragerc`, `.importlinter`, `.pre-commit-config.yaml`, `sonar-project.properties`, `CHANGELOG.md`.
- **Add** the `openspec/` spine (config + pinned `meaningfy` schema + `specs/` + `changes/`) — done by
  this change — and install the `/opsx:*` core profile.
- **Add** canonical `CLAUDE.md` + `AGENTS.md` symlink + `.claude/memory/MEMORY.md` index.
- **Replace** `setup.cfg` + `requirements/*.txt` dependency management with Poetry `[dependency-groups]`. **BREAKING** for contributors' install flow (`make install` instead of `pip install -r`).
- **Replace** flake8 with Ruff; add mypy.
- **BREAKING (runtime baseline):** raise Python floor 3.8 → 3.12 and bump core dependencies to current majors.
- **Reorganize** `tests/` into `unit/feature/e2e/integration` with a marker-injection `conftest.py` and a ≥80% coverage gate.
- **Migrate** `docs/` from Sphinx to an Antora component (Diátaxis IA).
- **Move** `docker/` → `infra/` (multistage non-root Dockerfile, layered env).
- **Replace** `.github/workflows/{test,package}.yml` with `ci.yaml` + `docs.yaml` that call `make` targets; add a `deploy.yaml` TODO stub.
- **Scaffold** `model/` (LinkML) + `make generate-models` seam (not yet generating).

## Capabilities

### New Capabilities
- `project-tooling`: the standardized build/lint/type/test/architecture toolchain and how `make` targets and CI gates compose it.
- `spec-spine`: the `openspec/` spine — artifact vocabulary (EPIC/PLAN/specs), the golden thread, and validation.
- `agentic-setup`: canonical `CLAUDE.md`/`AGENTS.md`/`.claude` conventions and the regenerable memory index.

### Modified Capabilities
<!-- None — no existing specs/ (this is the first change); no runtime behaviour requirements change. -->

## Impact

- **Code:** no logic changes; import roots unchanged (no `/src` lift, no `domain` rename). Touch points
  are config files, `tests/` layout, `docs/`, `infra/`, and dependency-driven API adjustments from the
  3.12/major bump (Flask/Connexion/Celery/rdflib/SPARQLWrapper call sites).
- **APIs:** the HTTP/CLI surface is unchanged; only the contributor install/run flow changes (Poetry).
- **Dependencies:** Python 3.8→3.12; major bumps across the stack.
- **Systems:** Docker image path moves (`docker/` → `infra/`); CI workflows replaced.
- **Out of scope / parked:** `load_versions.sh → Python` rewrite (separate PR).
