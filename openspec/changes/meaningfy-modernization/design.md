# PLAN (design) — rdf-differ modernization

> Parent: EPIC "Bring rdf-differ up to the Meaningfy standard" (`proposal.md`, this change).

## Context

`rdf-differ` is a Flask/Connexion API + Flask UI + Celery worker + Click CLI, packaged as a top-level
`rdf_differ/` package (no `/src`). Current baseline: Python 3.8, flake8, `setup.cfg` + `requirements/`,
Sphinx docs, top-level `docker/`, CI inlining commands. Layers already exist by convention
(`domain/ adapters/ services/ entrypoints/` + `utils/`) but nothing enforces them. The full gap audit
is preserved in `inputs/gap-analysis.md`. The in-flight `load_versions` rewrite is parked on its own
branch; this change is a separate branch off `master`.

## Goals / Non-Goals

**Goals:**
- Every Meaningfy non-negotiable satisfied: no `/src` (already true), all tool config in root, canonical
  `CLAUDE.md` + `AGENTS.md` symlink, minimal `pyproject.toml`, `openspec/` spine projected.
- Canonical stack adopted (Poetry, Ruff, mypy, pytest+bdd, coverage ≥80%, import-linter, Antora, Make).
- Python floor 3.12; dependencies on current majors.
- `make install && make check-all` green at the end of every slice.

**Non-Goals:**
- No runtime behaviour change; no new features; the `load_versions` rewrite stays parked.
- No `domain → models` rename (DEC-2); no `/src` lift; no LinkML codegen (DEC-6); no live deploy (DEC-7).

## Decisions

- **Keep `domain/`** (DEC-2): the spine `config.yaml` treats `domain` as the innermost layer; the global
  prompt's `models/` is an alias, not a mandate. Renaming = churn across every import for no gain.
- **Poetry over pip-tools** (DEC-5): lockfile + dependency-groups; deps lifted from `requirements/common.txt`
  (runtime) and `requirements/dev.txt` (a `dev` group); `requirements/*.txt` + the `[tool:pytest]`/`[flake8]`
  blocks in `setup.cfg` are retired into dedicated root configs.
- **Dependency bump bound to the Python bump** (DEC-3): do 3.8→3.12 and the major bumps in one focused
  slice *after* tooling/tests exist, so the test suite catches regressions. Bumps that break and can't
  be fixed within appetite get pinned + a follow-up issue, not a rushed rewrite.
- **import-linter two-step** (DEC, architecture-guardrails): start with a permissive contract that only
  asserts the layered order; harden to per-layer forbidden-import contracts once layers are stable.
- **CD as a stub** (DEC-7): `deploy.yaml` is a marked TODO; `ci.yaml` + `docs.yaml` are live.

## Algorithm / approach

The migration is the ordered slice list in `tasks.md`, least-risk first. The mechanical gap-fill uses
`scaffold.sh --skip-existing` (adds missing files, never overwrites); per-file *migrations* (pyproject
normalization, flake8→Ruff, test reorg, Sphinx→Antora) are deliberate manual edits guided by the
`project-setup` references. Each slice is one commit/PR-section behind `make check-all`.

Worked example — the dependency-bump slice (highest risk):
1. Branch is already green on 3.8 deps after the Poetry slice.
2. Bump `requires-python` to `>=3.12`; update `ruff.toml`/`mypy.ini` target version.
3. Bump deps group-by-group: rdflib/SPARQLWrapper first (core), then Flask/Connexion, then Celery/redis.
4. After each group: `make check-all`. Fix call-site breakage in the *same* group's commit.
5. Any dep that can't be migrated within appetite → pin to its last-working major + open a follow-up.

### Anti-patterns
- ❌ Mixing the dep bump or the test reorg with any other concern in one commit.
- ❌ Merging a slice on a red `make check-all`.
- ❌ Renaming `domain/` or lifting to `/src` (explicit no-gos).
- ❌ Hand-migrating every Sphinx page 1:1 instead of porting the Diátaxis IA + essential content.
- ❌ "Fixing" lint debt surfaced by Ruff inside the tooling-swap config commit — debt fixes get their own commits.
- ❌ Generating LinkML models in this change (seam only, DEC-6).

## Error matrix

| Failure mode | Expected handling |
|---|---|
| A dependency major bump breaks call sites beyond appetite | Pin to last-working major, open a follow-up issue, continue. |
| `make check-all` red after a slice | Do not proceed/merge; fix or revert that slice (small steps make it attributable). |
| import-linter flags a real layer violation | Fix in a dedicated commit; if structural, downgrade contract + file a follow-up. |
| Antora build fails / content gap | Keep Sphinx output until Antora builds; port IA first, content incrementally. |
| Poetry lock conflicts on 3.12 | Resolve per-group; if unresolvable, isolate the offending dep and pin. |
| Parked stash / load_versions branch disturbed | Never touch it; modernization only adds to its own branch. |

## Risks / Trade-offs

- **[Wide dependency blast radius]** → bind bumps to the test suite; group-by-group; pin-and-defer escape hatch.
- **[Contributor disruption from Poetry]** → update `INSTALL.md`/`CONTRIBUTING.md` + `make install` in the same slice; announce in CHANGELOG.
- **[Long-lived branch drifting from master]** → land additive slices fast and merge incrementally where possible; rebase regularly.
- **[Scope creep into behaviour]** → enforced by the no-gos; reviewer checks diffs touch no diffing logic.

## Open Questions

- **OQ-1**: ✅ RESOLVED (2026-06-18) — keep `domain/` (DEC-2 confirmed); no rename to `models/`.
- **OQ-2**: ✅ RESOLVED (2026-06-18) — land as **one PR** (`feature/meaningfy-modernization`) with
  **slice-per-commit** (the 9 task groups = 9 reviewable commits).
- **OQ-3**: Which dependency majors are in-appetite to fully migrate now vs pin-and-defer (esp. Connexion 2→3,
  which changes the API wiring)? Resolve at the dep-bump slice (5).
- **OQ-4**: Keep the gitnexus skills/`.gitnexus` index as part of the agentic setup, or drop them? (Assumed keep; resolve at slice 2.)
