> EPIC: rdf-loading-module — Rewrite the SKOS-History version-loading & delta-computation script in Python (this change's `proposal.md`)

The 10 TDD tasks of the RDF Loading Module, ported from
`inputs/IMPLEMENTATION-PLAN-rdf-loading-module.md`. Each task is test-first
(write failing test → run/verify fail → minimal implementation → verify pass → commit) and stays
within its cosmic-python layer. Full per-task code (failing tests + implementations) lives verbatim
in `inputs/IMPLEMENTATION-PLAN-rdf-loading-module.md`; ADRs, file structure, migration and
self-review are in `design.md`.

> **For agentic workers:** use superpowers:subagent-driven-development (fresh subagent per task,
> review between tasks) or superpowers:executing-plans.

## Task 1: Domain config models

- [ ] Write failing tests for `VersionStoreConfig.validate()`: rejects <2 versions, duplicate ids, missing file, relative IRI; `BlankNodePolicy.SKOLEMISE` rejected as "not yet supported" (ADR-5)
- [ ] Implement `rdf_differ/domain/loading/config.py` — `VersionSpec`, `VersionStoreConfig`, `LoadMode`, `BlankNodePolicy`, `ConfigError` (frozen dataclasses; `validate()` returns self)
- [ ] Add `ResolvedVersionMeta` + `resolve_version_meta()` (config-driven id/date resolution, F7/F14; replaces the `agrovoc jel` hack) with tests: data wins → config fallback → both absent
- [ ] *Layers:* models. *Deps:* none. *AC:* T1 passes; no framework imports
- [ ] Commit: `feat(loading): typed version-store config model`

## Task 2: UriBuilder

- [ ] Write failing tests: skos-history IRIs (history/version/record/delta/delta-graph), percent-encode unsafe ids, strip trailing slash
- [ ] Implement `rdf_differ/domain/loading/uris.py` — `UriBuilder` (mirrors `load_versions.sh:317-342`)
- [ ] *Layers:* models. *Deps:* none. *AC:* T2 passes
- [ ] Commit: `feat(loading): UriBuilder for skos-history IRIs`

## Task 3: Delta-pair math

- [ ] Write failing tests: 2 versions → single pair; consecutive + direct-to-current with no penultimate duplicate (spec §9.8)
- [ ] Implement `rdf_differ/domain/loading/delta_pairs.py` — `consecutive_pairs`, `direct_to_current_pairs`, `all_delta_pairs`
- [ ] *Layers:* models. *Deps:* none. *AC:* T4 passes
- [ ] Commit: `feat(loading): delta-pair computation`

## Task 4: GraphStorePort + query templates

- [ ] Write failing tests: `delta_update` targets correct graphs, uses `MINUS`, applies `isIRI` filter for `EXCLUDE` and no filter for `DOCUMENT_ONLY`
- [ ] Implement `rdf_differ/adapters/loading/queries.py` — `PREFIXES`, `BLANK_NODE_FILTERS`, `delta_update`, `clear_graph` (constants; no free strings)
- [ ] Add metadata template builders (each with a unit test): `service_description_update` (F4), `history_set_update` (F5), `version_record_update` (F6), `prev_link_update` (F8), `delta_metadata_update` (F11), `register_named_graph_update` (F15), `ask_graph_nonempty`/`ask_invalid_insertion`/`ask_invalid_deletion` (validation)
- [ ] Implement `rdf_differ/adapters/loading/graph_store_port.py` — `GraphStorePort` Protocol (`load_graph`, `run_update`, `ask`, `count_graph`, `serialize_graph`, `clear_graph`), `GraphStoreError`
- [ ] *Layers:* adapters (+ models). *Deps:* 1. *AC:* templates parametrised, no free strings
- [ ] Commit: `feat(loading): GraphStorePort and parametrised query templates`

## Task 5: PyoxigraphInMemoryStore adapter

- [ ] Write failing tests: insertions = new − old; blank nodes excluded under `EXCLUDE`
- [ ] Add `pyoxigraph~=0.5` to `requirements/common.txt`
- [ ] Implement `rdf_differ/adapters/loading/in_memory_store.py` — `PyoxigraphInMemoryStore` (bulk_load/update/query/dump/clear; translate errors to `GraphStoreError`)
- [ ] *Layers:* adapters. *Deps:* 2. *AC:* T3, T7 pass in-memory
- [ ] Commit: `feat(loading): pyoxigraph in-memory GraphStore adapter`

## Task 6: RemoteSparqlStore adapter

- [ ] Write failing tests (mocked HTTP): `load_graph` uses GSP `PUT ?graph=`; ≥400 status → `GraphStoreError`
- [ ] Implement `rdf_differ/adapters/loading/remote_store.py` — `RemoteSparqlStore` (GSP PUT, SPARQL Update POST, ASK/COUNT/serialize GET; injected `http_client`)
- [ ] *Layers:* adapters. *Deps:* 2. *AC:* T8 passes (mocked)
- [ ] Commit: `feat(loading): remote Fuseki GraphStore adapter (GSP + Update)`

## Task 7: VersionStoreLoader service

- [ ] Write failing tests with a `FakeStore(GraphStorePort)` recording an event log: all versions loaded before any delta (F12 two-pass order); each delta graph CLEARed before INSERTed (L5 idempotency); pair coverage
- [ ] Implement `rdf_differ/services/loading/loader.py` — `VersionStoreLoader.run()` orchestration (validate → service desc + history set → per-version load+record+register → prev links → per-pair clear+insertions+deletions+metadata+register → return `{dataset_id, current_version, delta_pairs, counts}`)
- [ ] Depends only on `GraphStorePort`, `UriBuilder`, `queries`, `delta_pairs`, `resolve_version_meta` — no `pyoxigraph`/`requests` import (enforced Task 10)
- [ ] *Layers:* services. *Deps:* 1–2. *AC:* T5, T6 pass
- [ ] Commit: `feat(loading): VersionStoreLoader orchestration service`

## Task 8: Validation service

- [ ] Write failing tests: empty version graph (`count_graph==0`) → `ValidationError`; invalid insertion triple (`ask` True) → `ValidationError`
- [ ] Implement `rdf_differ/services/loading/validation.py` — spec §10 structural + content `ASK`/`count_graph` checks; `ValidationError` names the offending graph
- [ ] *Layers:* services. *Deps:* 5. *AC:* T7 passes
- [ ] Commit: `feat(loading): post-load structural and content validation`

## Task 9: CLI entrypoint

- [ ] Write failing test with `click.testing.CliRunner`: `load --config x.yaml --mode in-memory --out dir` → exit 0, `result.json` with `validation: passed`
- [ ] Implement `rdf_differ/entrypoints/cli/load.py` — parse YAML → validate config → build store by `--mode` → run loader → validate → write serialised graphs + `result.json` (entrypoint only parses/wires/formats)
- [ ] *Layers:* entrypoints. *Deps:* 5–6. *AC:* in-memory CLI happy path
- [ ] Commit: `feat(loading): CLI for in-memory and remote diffs`

## Task 10: Integrate dual-mode, add contracts, retire the script

- [ ] Write parity test (T6): same fixtures through `RemoteSparqlStore` (stubbed Fuseki) and `PyoxigraphInMemoryStore` → identical counts + named-graph IRI set; existing `dataset_description`/`count_inserted_triples`/`count_deleted_triples` still correct
- [ ] Add `make_gsp_endpoint` helper to `FusekiDiffAdapter`; rewire `create_diff` (`diff_adapter.py:146-168`) to build `RemoteSparqlStore` + run `VersionStoreLoader` + `validate_store`; remove `SKOSHistoryRunner().run()`
- [ ] Add `.importlinter` — layers contract (`entrypoints > services > adapters > domain`) + store-seam forbidden contract (`rdf_differ.services.loading` must not import `pyoxigraph`/`requests`/`SPARQLWrapper`)
- [ ] Run `pytest -q` + `lint-imports`; delete `resources/load_versions.sh` and the subprocess path in `skos_history_wrapper.py`; adapt `prepare_config.feature` / `execute_skos_history.feature`
- [ ] *Layers:* adapters/services. *Deps:* 4–6. *AC:* existing API/Celery diff flow green; contracts pass
- [ ] Commit: `feat(loading): dual-mode cutover; retire load_versions.sh; enforce contracts`
