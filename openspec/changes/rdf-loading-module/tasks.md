> EPIC: rdf-loading-module — Rewrite the SKOS-History version-loading & delta-computation script in Python (this change's `proposal.md`)

The TDD task checklist for the RDF Loading Module in its **final agreed shape** (see `design.md`
DEC-1…DEC-10). Each task is test-first (write failing test → run/verify fail → minimal implementation →
verify pass → commit) and stays within its cosmic-python layer. Order: domain models+config → URIs +
delta-pair math → port + query templates → the three store adapters → loader → validation → in-memory
diff artifacts → CLI → API/Celery → remote-mode cutover → utils dissolution → stricter import-linter →
[gated] in-memory full report. ADRs/decisions, file structure, the `GraphStorePort` interface,
migration and self-review are in `design.md`.

> **For agentic workers:** use superpowers:subagent-driven-development (fresh subagent per task,
> review between tasks) or superpowers:executing-plans.

## Implementation status (2026-06-19)

**Implemented & green** (≈100 new tests; `make check-quality` passes — ruff, mypy, 4 import-linter
contracts): Tasks **1–12, 4b, 14, 15** — the full module (pydantic domain config/URIs/delta-pairs/
blank-node strategy/constants/errors/results; `GraphStorePort` + parametrised queries; `PyoxigraphStore`,
`RdflibStore`, `RemoteSparqlStore` + `StoreSettings` + `build_graph_store`; deterministic rdflib
skolemiser; `VersionStoreLoader` + validation + in-memory artifacts; `diff_service`; Click CLI), plus
the `utils/` dissolution, the tightened import-linter, and the `domain/model.py` pydantic migration.

**Task 13 (cutover) — flag-gated, not yet a deletion.** The Celery `create_diff` task runs the Python
loader when `RDF_DIFFER_USE_PYTHON_LOADER=true` (default off → legacy script). The diff logic is
unit-verified for parity on real engines; **deleting `load_versions.sh` + `skos_history_wrapper`**
is the final step, gated on a **Fuseki parity smoke test** (only validatable against a live endpoint).

**Task 16 (in-memory full report) — gated/deferred** on the external eds4jinja2 enhancement; the CLI
`--report` prints the documented fallback and still emits diff artifacts (DEC-5).

## Task 1: Domain config models (pydantic v2) — DEC-3

- [ ] Write failing tests for `VersionStoreConfig`: rejects <2 versions, duplicate ids, missing file, relative scheme/base IRI, mixed RDF formats; `BlankNodePolicy` ∈ {exclude, document_only, skolemise} **all accepted** (DEC-9 — skolemise is now supported); `engine` ∈ {remote, oxigraph, rdflib}
- [ ] Implement `rdf_differ/domain/loading/config.py` — `VersionSpec`, `VersionStoreConfig`, `Engine`/`LoadMode`, `BlankNodePolicy`, `ConfigError` as **pydantic v2** models with field/model validators (validation at construction)
- [ ] Add the pure `BlankNodeStrategy` interface + `BlankNodePolicy` enum in `rdf_differ/domain/loading/blank_nodes.py` (domain; no rdflib — concrete rdflib skolemiser is Task 4b) — DEC-9
- [ ] Add `ResolvedVersionMeta` + `resolve_version_meta()` (config-driven id/date resolution, F7/F14; replaces the `agrovoc jel` hack) with tests: data wins → config fallback → both absent
- [ ] *Layers:* domain. *Deps:* none. *AC:* T1 passes; pydantic allowed, no I/O-framework imports
- [ ] Commit: `feat(loading): typed pydantic version-store config model`

## Task 2: UriBuilder

- [ ] Write failing tests: skos-history IRIs (history/version/record/delta/delta-graph), percent-encode unsafe ids, strip trailing slash
- [ ] Implement `rdf_differ/domain/loading/uris.py` — `UriBuilder` (mirrors `load_versions.sh:317-342`)
- [ ] *Layers:* domain. *Deps:* none. *AC:* T2 passes
- [ ] Commit: `feat(loading): UriBuilder for skos-history IRIs`

## Task 3: Delta-pair math

- [ ] Write failing tests: 2 versions → single pair; consecutive + direct-to-current with no penultimate duplicate (spec §9.8); direct-to-current disabled → consecutive only
- [ ] Implement `rdf_differ/domain/loading/delta_pairs.py` — `consecutive_pairs`, `direct_to_current_pairs`, `all_delta_pairs`
- [ ] *Layers:* domain. *Deps:* none. *AC:* T4 passes
- [ ] Commit: `feat(loading): delta-pair computation`

## Task 4: GraphStorePort + query templates

- [ ] Write failing tests: `delta_update` targets correct graphs, uses `MINUS`, applies `isIRI` filter for `EXCLUDE` and no filter for `DOCUMENT_ONLY`
- [ ] Implement `rdf_differ/adapters/loading/queries.py` — `PREFIXES`, `BLANK_NODE_FILTERS`, `delta_update`, `clear_graph` (constants; no free strings)
- [ ] Add metadata template builders (each with a unit test): `service_description_update` (F4), `history_set_update` (F5), `version_record_update` (F6), `prev_link_update` (F8), `delta_metadata_update` (F11), `register_named_graph_update` (F15), `ask_graph_nonempty`/`ask_invalid_insertion`/`ask_invalid_deletion` (validation)
- [ ] Implement `rdf_differ/adapters/loading/graph_store_port.py` — `GraphStorePort` Protocol (`put_graph`, `clear_graph`, `update`, `query`, `serialize`), `GraphStoreError`
- [ ] *Layers:* adapters (+ domain). *Deps:* 1. *AC:* templates parametrised, no free strings
- [ ] Commit: `feat(loading): GraphStorePort and parametrised query templates`

## Task 4b: Blank-node SKOLEMISE strategy (rdflib, deterministic) — DEC-9

- [ ] Write failing tests: `skolemise` replaces blank-node statements with **W3C `.well-known/genid/`** Skolem IRIs; the transform is **deterministic** (same input ⇒ identical Skolem IRIs across runs / parse order); `de_skolemize` round-trips; `EXCLUDE`/`DOCUMENT_ONLY` paths unaffected
- [ ] Implement `rdf_differ/adapters/loading/skolemizer.py` — `rdflib.compare.to_canonical_graph` (deterministic labels) → `Graph.skolemize(authority=<dataset base>, basepath="/.well-known/genid/")`, exposed via the domain `BlankNodeStrategy` interface; applied to parsed RDF **before load** (engine-agnostic, both modes)
- [ ] *Layers:* adapters (imports `rdflib` — never in `domain`, per DEC-8). *Deps:* 1. *AC:* deterministic skolem IRIs; the interface admits a later URDNA2015 upgrade with no API change
- [ ] Commit: `feat(loading): deterministic W3C skolemisation blank-node strategy`

## Task 5: PyoxigraphStore adapter (in-memory) — DEC-2

- [ ] Write failing tests: insertions = new − old; blank nodes excluded under `EXCLUDE`
- [ ] Add `pyoxigraph` to `requirements/common.txt`
- [ ] Implement `rdf_differ/adapters/loading/in_memory_oxigraph_store.py` — `PyoxigraphStore` (`put_graph`/`update`/`query`/`serialize`/`clear_graph`; translate errors to `GraphStoreError`)
- [ ] *Layers:* adapters. *Deps:* 2, 4. *AC:* T3, T7 pass on the oxigraph engine
- [ ] Commit: `feat(loading): pyoxigraph in-memory GraphStore adapter`

## Task 6: RdflibStore adapter (in-memory) — DEC-2

- [ ] Write failing tests: insertions = new − old; blank nodes excluded under `EXCLUDE`; same named-graph IRI set as the oxigraph engine
- [ ] Implement `rdf_differ/adapters/loading/in_memory_rdflib_store.py` — `RdflibStore` over `rdflib` (`Dataset`/`ConjunctiveGraph` + SPARQL Update/Query); translate errors to `GraphStoreError`
- [ ] *Layers:* adapters. Independent of `in_memory_oxigraph_store` and `remote_store` (DEC-8). *Deps:* 2, 4. *AC:* engine parity with Task 5 on the same fixtures
- [ ] Commit: `feat(loading): rdflib in-memory GraphStore adapter`

## Task 7: RemoteSparqlStore adapter + store settings/factory — DEC-2/DEC-4/DEC-10

- [ ] Write failing tests (mocked HTTP): `put_graph` uses GSP `PUT ?graph=`; `update` POSTs SPARQL Update; `query` GETs ASK/COUNT; ≥400 status → `GraphStoreError`; transient failures retried per policy; `StoreSettings` binds `RDF_DIFFER_*` env; `build_graph_store(engine, settings)` returns the right adapter (in-memory engines ignore settings)
- [ ] Implement `rdf_differ/adapters/loading/remote_store.py` — `RemoteSparqlStore` against **any SPARQL 1.1 endpoint**, connection via **injected `StoreSettings`** (never reads env itself), injected `http_client`
- [ ] Implement `rdf_differ/adapters/loading/settings.py` (`StoreSettings`, pydantic-settings, env `RDF_DIFFER_*`) and `store_factory.py` (`build_graph_store`); add `pydantic-settings` to deps (DEC-10)
- [ ] *Layers:* adapters. Independent of the two in-memory adapters (DEC-8). *Deps:* 2, 4, 5, 6. *AC:* T8 passes (mocked); factory selects all three engines
- [ ] Commit: `feat(loading): remote SPARQL adapter + StoreSettings/build_graph_store factory`

## Task 8: VersionStoreLoader service

- [ ] Write failing tests with a `FakeStore(GraphStorePort)` recording an event log: all versions loaded before any delta (F12 two-pass order); each delta graph CLEARed before INSERTed (L5 idempotency); pair coverage; engine-agnostic (same log under any injected store)
- [ ] Implement `rdf_differ/services/loading/loader.py` — `VersionStoreLoader.run()` (validate → service desc + history set → per-version load+record+register → prev links → per-pair clear+insertions+deletions+metadata+register → return `{dataset_id, current_version, delta_pairs, counts}`)
- [ ] Depends only on `GraphStorePort`, `UriBuilder`, `queries`, `delta_pairs`, `resolve_version_meta` — no `pyoxigraph`/`rdflib`/`requests`/`SPARQLWrapper`/`eds4jinja2` import (enforced Task 15)
- [ ] *Layers:* services. *Deps:* 1–4. *AC:* T5, T6 pass
- [ ] Commit: `feat(loading): VersionStoreLoader orchestration service`

## Task 9: Validation service

- [ ] Write failing tests: empty version graph (`query` count == 0) → `ValidationError`; invalid insertion triple (`ask` True) → `ValidationError`; parse failure → `GraphLoadError` naming the version
- [ ] Implement `rdf_differ/services/loading/validation.py` — spec §10 structural + content `ASK`/count checks; `ValidationError` names the offending graph
- [ ] *Layers:* services. *Deps:* 8. *AC:* T7 passes
- [ ] Commit: `feat(loading): post-load structural and content validation`

## Task 10: In-memory diff artifacts (no external dependency) — DEC-5

- [ ] Write failing tests: serialise the four named graphs to files; emit `{counts, validation}`; works on both in-memory engines
- [ ] Implement `rdf_differ/services/loading/artifacts.py` — serialise via `GraphStorePort.serialize` + assemble the result document
- [ ] *Layers:* services. *Deps:* 5, 6, 8, 9. *AC:* artifacts produced in-memory with no triple store and no eds4jinja2
- [ ] Commit: `feat(loading): in-memory diff artifacts output`

## Task 11: CLI entrypoint — DEC-6/DEC-10

- [ ] Write failing test with `click.testing.CliRunner`: `load --config x.yaml --engine oxigraph --out dir` → exit 0, `result.json` with `validation: passed`; `--engine rdflib` likewise; `--engine remote` builds the remote store from `StoreSettings` (env), and `--endpoint …` overrides it
- [ ] Implement `rdf_differ/entrypoints/cli/load.py` — parse YAML → validate `VersionStoreConfig` → `build_graph_store(engine, StoreSettings(...))` (with CLI overrides) → run loader → validate → write serialised graphs + `result.json` (entrypoint only parses/wires/formats)
- [ ] *Layers:* entrypoints. *Deps:* 5–7, 10. *AC:* in-memory CLI happy path on both engines; remote uses env settings with `--endpoint` override
- [ ] Commit: `feat(loading): CLI for remote and in-memory diffs`

## Task 12: API + Celery integration — DEC-6

- [ ] Write failing test: the create-diff endpoint accepts `engine`/`mode`; the Celery task builds the store for the task lifetime, reports status, and honours the revoke/cancel queue (`adapters/redis.py`)
- [ ] Implement the endpoint param + worker wiring (in-memory store built inside the worker; for `--report`, the eds4jinja2 in-memory wiring per Task 16 when present)
- [ ] *Layers:* entrypoints/adapters. *Deps:* 5–8, 11. *AC:* async create-diff works for all three engines
- [ ] Commit: `feat(loading): engine-parameterised async create-diff via Celery`

## Task 13: Remote-mode cutover — retire load_versions.sh — DEC-4

- [ ] Write parity test (T6): same fixtures through `RemoteSparqlStore` (stubbed endpoint) and both in-memory engines → identical counts + named-graph IRI set; existing `dataset_description`/`count_inserted_triples`/`count_deleted_triples` still correct
- [ ] Add the GSP `/data` endpoint helper to `FusekiDiffAdapter`; rewire `create_diff` (`diff_adapter.py:146-168`) to build `RemoteSparqlStore` + run `VersionStoreLoader` + `validate_store`; remove `SKOSHistoryRunner().run()`
- [ ] Delete `resources/load_versions.sh` and the subprocess path in `skos_history_wrapper.py:192-213`; adapt `prepare_config.feature` / `execute_skos_history.feature`
- [ ] *Layers:* adapters/services. *Deps:* 7, 8. *AC:* existing API/Celery diff flow green; four-graph contract preserved
- [ ] Commit: `feat(loading): remote-mode cutover; retire load_versions.sh and subprocess`

## Task 14: utils/ dissolution — DEC-7

- [ ] Move `file_utils` filesystem ops + `rdf_converter` → `rdf_differ/adapters/filesystem.py` (adapters); `INPUT_MIME_TYPES` + `check_dataset_name_validity`/`build_unique_name`/`build_secure_filename` → domain; `build_dataset_reports_location`/`read_meta_file` → services (report); `conversions.strtobool` → a config helper
- [ ] Update all consumers (incl. `tests/steps/*.py`, `services/report_handling.py`) and run the suite green
- [ ] Remove `rdf_differ/utils/` and drop its two import-linter contracts
- [ ] *Layers:* cross-layer move. *Deps:* none (independent cleanup). *AC:* `rdf_differ/utils/` gone; tests green
- [ ] Commit: `refactor: dissolve rdf_differ/utils into the proper layers`

## Task 15: Stricter import-linter — DEC-8

- [ ] Update `.importlinter`: keep the (utils-free) layers contract (`entrypoints > services > adapters > domain`); add forbidden contract — `rdf_differ.services` must not import `pyoxigraph`/`rdflib`/`requests`/`SPARQLWrapper`/`eds4jinja2`; add forbidden — `rdf_differ.domain` must not import I/O frameworks (`flask`/`connexion`/`celery`/`click`/`requests`/`rdflib`/`pyoxigraph`/`eds4jinja2`); add independence — the three store adapter modules must not import each other
- [ ] Run `lint-imports` (`make check-architecture`) green
- [ ] *Layers:* architecture. *Deps:* 8, 14. *AC:* all contracts pass; pydantic-in-domain allowed
- [ ] Commit: `chore: tighten import-linter contracts (store seam, domain purity, adapter independence)`

## Task 16: [GATED on the eds4jinja2 epic — OPTIONAL] In-memory full report — DEC-5

> **Gated / optional.** Depends on the external eds4jinja2 enhancement (its own epic in the eds4jinja2
> repo, separate thread): `ReportBuilder(external_data_source_builders=…)` + an engine-agnostic
> `InMemorySPARQLDataSource`. **If that release is absent, do NOT block:** `--report` on an in-memory
> engine falls back to remote-only (clear message) — **no rework of Tasks 1–15**.

- [ ] Write failing test: with the eds4jinja2 enhancement present, `load --engine oxigraph --report` renders a full report by querying the in-process store (templates untouched); with it absent, `--report` falls back to remote-only and says so
- [ ] Implement `rdf_differ/services/loading/report.py` — override `from_endpoint` to query the in-process store via `GraphStorePort`; wire `external_data_source_builders`; implement the graceful fallback
- [ ] *Layers:* services. *Deps:* 10, 11, eds4jinja2 release. *AC:* full report in-memory when the capability is present; documented fallback otherwise
- [ ] Commit: `feat(loading): in-memory full report via eds4jinja2 enhancement (with remote-only fallback)`
