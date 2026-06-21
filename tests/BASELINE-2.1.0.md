# Test baseline: release 2.1.0 (for cross-version comparison)

Release **`2.1.0`** (git tag `2.1.0`, published 2026-01-28) is the **frozen baseline** for comparing
the test suite and fixtures before the FastAPI + component-first modernization. Everything from 2.1.0
is permanently reserved in git at that tag — nothing was deleted from history.

> Maintained for @Rashif: take the 2.1.0 tests/data as the reference and compare functionality of the
> new features against them. Principle: **preserve as much as possible, extend; change only what the
> upgrade forces.**

## Retrieve / compare the 2.1.0 baseline

```bash
# See the whole 2.1.0 test tree
git ls-tree -r --name-only 2.1.0 -- tests/

# Diff any file against 2.1.0
git diff 2.1.0 HEAD -- tests/

# Check out the 2.1.0 tests into a scratch dir for side-by-side comparison
git archive 2.1.0 tests/ | tar -x -C /tmp/rdf-differ-2.1.0-tests
```

## What is preserved vs. changed vs. added (2.1.0 → current)

### Test data — IDENTICAL ✅
`tests/test_data/` is byte-for-byte unchanged (51 files at 2.1.0 and now; empty diff). All existing
RDF samples, application-profile configs (`sample_ap_config/ap1`, `ap2`), OWL/SHACL/eurovoc/cob
fixtures are reused as-is by the new tests (epic decision: reuse existing data, no new heavy fixtures).

### Gherkin feature specs — PRESERVED ✅
The behaviour scenarios are intact:
- `prepare_config.feature` — identical.
- `diffing_two_dataset_versions.feature`, `execute_skos_history.feature`, `owl_diff.feature`,
  `inventory_of_diffs.feature` — unchanged scenarios; only a leading `@integration` tag was added so
  the default `make test-feature` run is infra-free (these need a live Fuseki/Redis/Celery stack).

### BDD step layout & implementations — RELOCATED + UPGRADED 🔁
- Steps moved `tests/steps/` → `tests/feature/` (and `tests/features/` holds the `.feature` files);
  `tests/fixtures/` folded into `tests/feature/conftest.py`.
- Step *implementations* were adapted (~30–110 lines each) to the **new import paths** (component-first:
  `rdf_differ.diffing.adapters…`, `rdf_differ.core.adapters…`) and the **FastAPI** entrypoints. The
  *what* (scenarios) is preserved; the *how* (wiring) changed because the packages and web framework
  changed. This is the expected upgrade divergence.

### Unit tests — MOSTLY EXTENDED, two REPLACED 🔁
Replaced because the web framework changed (Connexion/Flask → FastAPI); behaviour is equivalent:
| 2.1.0 (removed) | Current replacement |
|---|---|
| `tests/unit/test_entrypoints_api_handlers.py` (Connexion handlers) | `tests/unit/test_api_routes.py` (FastAPI TestClient) |
| `tests/unit/test_entrypoints_ui_views.py` (Flask views) | `tests/unit/test_ui_routes.py` + `test_ui_api_client.py` (FastAPI + httpx) |

Everything else from 2.1.0's unit tests is retained, plus substantial **new** coverage: the whole
`tests/unit/loader/**` suite, `test_api_routes`, `test_ui_routes`, `test_ui_api_client`,
`test_entrypoint_logging`, and new BDD features (`reporting`, `web_ui`, `rest_api`,
`loading_diff_edge_cases`, `cli_load`, `remote_diff_pipeline`).

## Working principle going forward

Unit tests and feature tests grow together for coverage; **feature (BDD) tests assert the sanity,
correctness and edge cases of the functionality** (loading & diffing, reporting, API, UI, CLI), while
unit tests pin per-layer logic. New features must extend — not silently drop — the behaviour proven at
2.1.0; any 2.1.0 scenario that cannot be kept is migrated to an equivalent and noted here.
