> Derived from EPIC "Bring rdf-differ up to the Meaningfy standard" (this change's `proposal.md`)

Ordered least-risk first. Each numbered group is one reviewable slice; every slice ends green on
`make check-all` before the next begins. `[~]` marks work already done while shaping this change.

## 0. Pre-flight (done while shaping)

- [x] 0.1 Drop 9 stale fully-merged branches; keep `master` + parked `feature/rewrite-load-versions-to-python`
- [x] 0.2 Park load_versions (stash floating agentic files); create `feature/meaningfy-modernization` off `master`
- [x] 0.3 Project the OpenSpec spine (config + pinned schema + specs/ + changes/) — this change lives here

## 1. Additive standalone configs (zero-risk)

- [ ] 1.1 Run `scaffold.sh --skip-existing` to drop in `ruff.toml`, `mypy.ini`, `pytest.ini`, `.coveragerc`, `.pre-commit-config.yaml`, `sonar-project.properties`, `CHANGELOG.md`
- [ ] 1.2 Add a **permissive** `.importlinter` (asserts only the layered order, not yet per-layer forbidden imports)
- [ ] 1.3 Verify nothing else changed; `make check-all` (lint may be advisory until slice 5)

## 2. Agentic files (canonical CLAUDE.md)

- [ ] 2.1 Author canonical `CLAUDE.md` (routing + project specifics + spine pointers + golden-thread note)
- [ ] 2.2 Symlink `AGENTS.md → CLAUDE.md` (DEC-4)
- [ ] 2.3 Add `.claude/memory/MEMORY.md` (≤200-line regenerable index); carry over gitnexus skills/index (OQ-4)
- [ ] 2.4 Commit `.mcp.json` (meaningfy MCP) onto this branch

## 3. pyproject / Poetry migration

- [ ] 3.1 Author minimal `pyproject.toml`: project metadata, `requires-python = ">=3.12"`, Poetry build
- [ ] 3.2 Lift runtime deps from `requirements/common.txt` (+ `prod.txt`) and dev deps from `requirements/dev.txt` into `[dependency-groups]`
- [ ] 3.3 Move the `[tool:pytest]` block from `setup.cfg` into `pytest.ini`; delete `[flake8]` (superseded by Ruff)
- [ ] 3.4 `poetry lock`; update `Makefile` `install` target; update `INSTALL.md`/`CONTRIBUTING.md`
- [ ] 3.5 Retire `requirements/*.txt` + emptied `setup.cfg`; `make install && make check-all`

## 4. Tooling swap (Ruff + mypy)

- [ ] 4.1 Wire Ruff (format+lint) and mypy into `Makefile` (`lint`, `format`, `typecheck`) and `.pre-commit-config.yaml`
- [ ] 4.2 Fix the lint debt Ruff surfaces — in dedicated commit(s), separate from config
- [ ] 4.3 Add mypy baseline (start lenient; tighten later); `make check-all`

## 5. Python 3.12 + dependency bumps (high blast radius — alone)

- [ ] 5.1 Confirm `requires-python = ">=3.12"`; point ruff/mypy target at 3.12
- [ ] 5.2 Bump rdflib / SPARQLWrapper / rdf_differ core deps; fix call sites; `make check-all`
- [ ] 5.3 Bump Flask / Flask-WTF / Flask-Bootstrap / Connexion (2→3 wiring); fix entrypoints; `make check-all`
- [ ] 5.4 Bump Celery / redis / flower; fix worker wiring; `make check-all`
- [ ] 5.5 Pin-and-defer any dep that exceeds appetite (open follow-up); record in CHANGELOG

## 6. Test tree reorganization

- [ ] 6.1 Introduce `tests/{unit,feature,e2e,integration}/` with the marker-injection `conftest.py`
- [ ] 6.2 Move existing `tests/unit/*` and `tests/features/*` + `tests/steps/*` into the new layout
- [ ] 6.3 Wire coverage gate `--cov-fail-under=80`; untrack committed artifacts (junit/cucumber/.coverage)
- [ ] 6.4 `make test` green with the gate

## 7. Architecture tightening

- [ ] 7.1 Harden `.importlinter` to real per-layer forbidden-import contracts (entrypoints→services→domain; adapters→domain)
- [ ] 7.2 Resolve violations (esp. `utils/` placement) in dedicated commits — only where the linter forces it
- [ ] 7.3 `make check-architecture` green

## 8. Pillars — docs, infra, model seam

- [ ] 8.1 Scaffold the Antora component (Diátaxis IA); port essential content from Sphinx; retire `docs/` Sphinx config
- [ ] 8.2 Move `docker/ → infra/` (multistage non-root Dockerfile, layered env); update compose + references
- [ ] 8.3 Scaffold `model/` (LinkML) + `make generate-models` **seam** (no generation yet, DEC-6)

## 9. CI / CD

- [ ] 9.1 Replace `.github/workflows/{test,package}.yml` with `ci.yaml` calling `make check-all`
- [ ] 9.2 Add `docs.yaml` (Antora build) + `openspec validate --strict` in CI
- [ ] 9.3 Add `deploy.yaml` TODO stub + boundary docs (DEC-7); set runner Python to 3.12

## Roadmap

- [ ] 1.1 · [ ] 1.2 · [ ] 1.3 · [ ] 2.1 · [ ] 2.2 · [ ] 2.3 · [ ] 2.4 · [ ] 3.1 · [ ] 3.2 · [ ] 3.3 · [ ] 3.4 · [ ] 3.5 · [ ] 4.1 · [ ] 4.2 · [ ] 4.3 · [ ] 5.1 · [ ] 5.2 · [ ] 5.3 · [ ] 5.4 · [ ] 5.5 · [ ] 6.1 · [ ] 6.2 · [ ] 6.3 · [ ] 6.4 · [ ] 7.1 · [ ] 7.2 · [ ] 7.3 · [ ] 8.1 · [ ] 8.2 · [ ] 8.3 · [ ] 9.1 · [ ] 9.2 · [ ] 9.3

## Verification

Each slice ends green on `make check-all` (Ruff + mypy + import-linter + pytest ≥80% + `openspec validate --strict`); the whole change is done when the `project-setup` Definition-of-Done checklist passes on the modernized repo with no runtime behaviour change.
