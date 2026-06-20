# PLAN — tasks: behaviour-test-coverage

Parent EPIC: `behaviour-test-coverage` (proposal.md) · Design: `design.md`. Test code only; each
feature lands with passing steps, `make test-unit`/`test-feature` green.

## T1 — Reporting feature (no infra)  (DEC-2, DEC-4)
- [ ] `tests/features/reporting.feature`: list APs, list variants, queries dict; negative unknown AP/variant/missing queries
- [ ] `tests/feature/test_reporting_steps.py`

## T2 — Web UI feature (no infra)  (DEC-3, DEC-4)
- [ ] `tests/features/web_ui.feature`: list, create happy→redirect, validation error, API-error flash, CSRF reject, view dataset, report download ok/fail, revoke
- [ ] `tests/feature/test_web_ui_steps.py` (FastAPI TestClient, mocked api_client)

## T3 — REST API feature (no infra)  (DEC-4)
- [ ] `tests/features/rest_api.feature`: list/get/create/build-report/tasks status codes + problem body + OpenAPI served
- [ ] `tests/feature/test_rest_api_steps.py` (TestClient, mocked services)

## T4 — Loading + diff edge/negative (no infra)  (DEC-1, DEC-4)
- [ ] `tests/features/loading_diff_edge_cases.feature`: identical versions → empty delta; blank nodes; missing file; format mismatch
- [ ] `tests/feature/test_loading_diff_edge_steps.py` (in-memory engines via diff_service)

## T5 — CLI feature (no infra)  (DEC-1, DEC-4)
- [ ] `tests/features/cli_load.feature`: `rdf-diff load --engine rdflib` happy → artifacts; negative bad args/missing file
- [ ] `tests/feature/test_cli_load_steps.py` (CliRunner)

## T6 — Remote pipeline (integration, infra)  (DEC-1)
- [ ] `tests/features/remote_diff_pipeline.feature` (`@integration`): create diff via API + poll task against a live stack
- [ ] step defs; `xfail` allowed while the legacy load_versions.sh pipeline is unfixed (rdf-loading-module epic)

## Done when
- [ ] New features pass under `make test-feature` (infra-free) with no service running
- [ ] `make check` stays green; coverage maintained ≥80%
- [ ] Coverage inventory in design.md reflects reality
