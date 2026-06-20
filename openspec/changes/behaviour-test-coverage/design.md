# PLAN — design: behaviour-test-coverage

> Parent EPIC: `openspec/changes/behaviour-test-coverage/proposal.md`. Test code only.

## Layout & conventions

- Features: `tests/features/<name>.feature`. Steps: `tests/feature/test_<name>_steps.py`
  (pytest-bdd `scenarios(...)`). Reuse `tests/feature/conftest.py`.
- Marker-by-path (`tests/conftest.py`) tags everything under `tests/feature/` as `feature`;
  infra-dependent scenarios add `@integration` (run with `-m integration` once a stack is up).
- Prefer `Scenario Outline` + `Examples` for multi-data cases (per house BDD style).

## Coverage inventory (exists → this epic adds)

| Capability | Exists | This epic adds |
|---|---|---|
| Loading + diff (in-memory) | `rdf_loading_module.feature`, `owl_diff.feature` | edge (identical versions, blank nodes) + negative (missing file, format mismatch) via `diff_service` |
| Diffing (remote/skos) | `diffing_two_dataset_versions`, `execute_skos_history`, `prepare_config` | leave as-is (legacy; `@integration`) |
| Reporting | — (unit only) | **new** `reporting.feature`: list APs, variants, queries; negative unknown AP/variant |
| REST API | unit route tests | **new** `rest_api.feature`: journey-level status + problem body + OpenAPI |
| Web UI | unit route tests | **new** `web_ui.feature`: list/create/validation/flash/CSRF/view/report/revoke |
| CLI | — | **new** `cli_load.feature`: `rdf-diff load` in-memory happy + negative |

## Test approach per capability

- **Loading/diff:** `build_diff_config(engine=Engine.RDFLIB|PYOXIGRAPH)` + `create_version_diff(store, config)`
  with a store from `graph_store_provider`. Assert `LoadResult` delta pairs / counts. Files from
  `tests/test_data/owl` (small ttl). No infra.
- **Reporting:** `ApplicationProfileManager` over `tests/test_data/sample_ap_config` (ap1/ap2).
  Assert `list_aps`, `list_template_variants`, `get_queries_dict`; negative raises `LookupError`/
  `FileNotFoundError`.
- **API/UI:** FastAPI `TestClient`; mock `api_client` / services with `unittest.mock`. Assert status,
  flashes, redirects, CSRF rejection.
- **CLI:** `click.testing.CliRunner` invoking `rdf_differ.loader.entrypoints.cli:cli` with
  `--engine rdflib` and a `tmp_path` out-dir; assert exit code + artifacts; negative bad args.

## Risk / notes

- If a scenario surfaces a real bug, mark `xfail(reason=..., strict=False)` with a link to the owning
  epic and move on (DEC-5) — do not fix production here.
- Keep features fast: use the smallest test-data files (`owl/ePO_sample-4.0.0.*.ttl`).
