# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **mypy is now green and gating** (`make check-quality` runs lint + types + architecture). Fixed
  all ~52 type errors: `Optional` defaults, missing annotations, `__eq__(self, other: object)`,
  `cast(...)` for untyped third-party returns, and removed the re-export indirection (consumers now
  import `build_dataset_reports_location` / `read_meta_file` from `utils.file_utils`). Per-module
  `ignore_missing_imports` for the stub-less libs (celery, connexion, flask_wtf, wtforms, pytz,
  requests, SPARQLWrapper, eds4jinja2).
- **Removed `distutils`** (removed from Python 3.12; it was working only via a fragile setuptools
  shim): `distutils.util.strtobool` → `rdf_differ.utils.conversions.strtobool`;
  `distutils.dir_util.copy_tree` → `shutil.copytree(..., dirs_exist_ok=True)`.

- **Infrastructure modernized and moved `docker/` → `infra/`** (compose, Dockerfiles, nginx, traefik,
  redis.conf; Makefile/README/compose references updated). Dockerfiles rebuilt on **Python 3.12 +
  Poetry + non-root**, installing from the lockfile (the old `pip -r requirements` is gone).
- **Connexion 3 serving migration:** the API is ASGI under Connexion 3 — it is now served by
  `gunicorn -k uvicorn.workers.UvicornWorker` on the ASGI app (`api.run:connexion_app`); the UI stays
  gunicorn WSGI. `bash/run_api.sh` updated (and its stale `adapters.celery` path fixed). Smoke-tested:
  the API boots under the Uvicorn worker and `GET /diffs`, `/ui/`, `/openapi.json` all return 200.
- **Secrets removed from version control:** `bash/.env`, `infra/.env`, `infra/.env-test` are
  untracked + git-ignored; committed `*.example` templates (placeholder values) added. `.gitignore`
  now blocks `.env`/`.env-test`; the Makefile `-include infra/.env` tolerates a fresh clone.
  ⚠️ Old secret values remain in git history — rotate `SECRET_KEY_*` and the Fuseki/Flower passwords.
- **LinkML `model/` seam** added (`model/schema.yaml` mirroring the domain + `make generate-models`).
  Seam only — generation is opt-in and not yet authoritative (DEC-6); the hand-written
  `rdf_differ/domain/model.py` remains the source of truth.

- **Modernization to the Meaningfy standard** (in progress, slice-per-commit):
  projected the OpenSpec spine; adding root tool configs (Ruff, mypy, coverage,
  import-linter, pre-commit, Sonar). Tooling/structure only — no runtime
  behaviour change. See `openspec/changes/meaningfy-modernization/`.
- **Packaging migrated to Poetry** with PEP 621 `[project]` + `[dependency-groups]`;
  `requirements/*.txt` and `setup.cfg` retired; pytest config moved to `pytest.ini`.
- **BREAKING (install flow):** install via `poetry install` (or `make install`),
  no longer `pip install -r requirements/...`.
- **BREAKING (runtime baseline):** Python floor raised to **3.12**; dependencies
  bumped to current majors — Flask 3, Connexion 3 (API app construction updated),
  Celery 5.4+, rdflib 7.1+, pandas 2.2+, etc.
- Dropped **Flask-Bootstrap** (unused; UI uses Materialize CSS via CDN).
- **Linting/formatting swapped to Ruff** (replaces flake8): auto-fixed ~77 issues, fixed
  bare-excepts/lambda/contextlib.suppress; deferred B904/N818 and test B008/F811 as documented
  debt. Added `make` targets `format`, `typecheck`, `check-architecture`, `check-quality`,
  `check-all`. mypy wired (canonical config) with a ~62-error legacy baseline tracked as debt
  (not yet gating).
- **Test tree reorganized** to the Meaningfy layout: `tests/feature/` (BDD step defs,
  renamed from `tests/steps/`), new `tests/e2e/` + `tests/integration/`, and a
  marker-injection `conftest.py` (markers applied by path; `pytest -m unit`). Strict
  markers enabled. Coverage gate wired at the current level (`fail_under=65`, ≈68%
  measured). Deduped two shadowed test names (F811).
- **Coverage raised to ≥80%** (gate `fail_under=80`): added focused unit tests for the
  previously-untested domain model and for `services/{queue,tasks}`, `adapters/sparql`,
  `utils/rdf_converter`, `ui/api_wrapper`, the query-profiler helpers, the task/AP API
  handlers, and `report_handling.build_report`. 153 unit tests, ~80.6% coverage.
- **Architecture boundaries fixed and enforced** (import-linter): the Celery task module
  moved `adapters/celery.py → services/celery.py` (task orchestration is the services
  layer); the pure path/IO helpers `build_dataset_reports_location` + `read_meta_file`
  moved to `utils/file_utils.py` (re-exported from `report_handling` for compatibility),
  so `adapters` no longer imports `services`. `.importlinter` now enforces the real chain
  `entrypoints > services > adapters > domain > utils` plus a utils-isolation contract
  (2 contracts kept). Behaviour-neutral (105/2 unchanged; Celery tasks still register).
  Updated the `celery -A` worker path in the compose files.
- **CI replaced** with `.github/workflows/ci.yaml` (Python 3.12, Poetry, `make check-quality`,
  `openspec validate --changes --strict`, unit tests with Redis + Fuseki service containers and
  the coverage gate, Codecov upload). Added a `deploy.yaml` CD **stub** pending DevOps ratification
  (DEC-7; legacy publish logic preserved in `.github/disabled-workflows/package.yml`). Removed the
  Python-3.8 `test.yml`/`package.yml`. Wrote the normative `specs/` deltas for the new capabilities
  (`project-tooling`, `spec-spine`, `agentic-setup`) so the change validates strictly.
  (Antora `docs.yaml` deferred with the docs pillar, slice 8.)
- **eds4jinja2 upgraded to the real `0.3.1`** from PyPI (3.12-compatible: pandas ~=2.2, numpy ~=1.26);
  the temporary `vendor/eds4jinja2/` workaround is removed. eds4jinja2 0.3.1 still pins `rdflib ~=7.0`
  and `requests ~=2.31`, so those are held at 7.0.x / 2.31.x here (raise once eds4jinja2 relaxes them).
