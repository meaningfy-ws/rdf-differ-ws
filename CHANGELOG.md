# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

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
  measured; the ≥80% target with new tests is deferred). Deduped two shadowed test
  names (F811). No new tests added. (TODO: reclassify the API-dependent UI tests from
  `unit/` into `integration/`.)
- **Temporary:** vendored a pin-relaxed copy of `eds4jinja2` under `vendor/eds4jinja2/`
  so it installs on 3.12 (upstream 0.2.0 caps pandas/numpy below their cp312 wheels).
  Remove once `eds4jinja2 >= 0.3.0` ships — see the upstream fix spec in the change.
