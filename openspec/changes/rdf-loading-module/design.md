# Design — RDF Loading Module

> Derived from EPIC "Rewrite the SKOS-History version-loading & delta-computation script in Python"
> (this change's `proposal.md`). This is the decisions/"how" half of the PLAN; the executable task
> breakdown is in `tasks.md`. Verbatim-first port of
> `inputs/IMPLEMENTATION-PLAN-rdf-loading-module.md` (header + ADRs + tech stack + file structure +
> migration + self-review).

**Goal:** Replace `resources/load_versions.sh` (run via subprocess from `skos_history_wrapper.py`)
with a layered, fully-tested Python RDF Loading Module that loads RDF versions and computes
skos-history delta graphs in **two interchangeable modes** — in-memory (pyoxigraph, no server) and
remote (Fuseki via HTTP).

**Architecture:** A single secondary-adapter port, `GraphStorePort`, isolates all triple-store
interaction. The loading **service** depends only on that port and on SPARQL template **constants**,
so the identical delta logic runs against either an in-memory `pyoxigraph.Store` or a remote SPARQL
endpoint, chosen by dependency injection. Domain models (config, URI builder, delta-pair math,
blank-node policy) carry no framework dependencies. A new CLI entrypoint exposes in-memory mode; the
existing API/Celery path is rewired to the remote adapter.

**Tech Stack:** Python 3.8+, `pyoxigraph` (new), `rdflib~=7.0` (already present, parsing/fallback),
`requests~=2.31` + `SPARQLWrapper~=2.0` (already present, remote transport), `click~=8.1` (CLI,
already present), frozen `dataclasses` (config — decided in Task 1; not pydantic), `pytest` +
`pytest-bdd` (tests), `import-linter` (new, contracts).

---

## Architectural Decision Records

These ADRs record the decisions the developer must **not** relitigate. Each weighs the real
alternatives and commits.

### ADR-1 (L3) — Isolate the triple store behind a single `GraphStorePort`

**Context.** Today the store is reached three incompatible ways: `curl` in bash (`load_versions.sh`),
`requests` for Fuseki admin (`diff_adapter.py`), and `SPARQLWrapper` for query/update (`sparql.py`).
Dual-mode is impossible while the store access is scattered and concrete.

**Considered options.**
1. **One port, two adapters (in-memory, remote).**
2. Two parallel services (one per backend) sharing helpers.
3. Keep `SPARQLWrapper` everywhere; run a local Fuseki for "in-memory".

**Decision:** Option 1.

**Consequences.** + Same delta logic both modes; + trivially mockable services; + future backends
(GraphDB, Oxigraph-server, RocksDB) are new adapters; − one abstraction layer to maintain; − port
must be the lowest-common-denominator of GSP + SPARQL Update.

**Pros and cons.**
- *Option 1:* Good, because it directly enables the core dual-mode bet (DIP). Good, because services become pure and testable. Bad, because the port surface must be designed carefully.
- *Option 2:* Good, because each path is simple. Bad, because delta logic is duplicated — the exact bug-farm the rewrite must kill.
- *Option 3:* Good, because zero new code paths. Bad, because "in-memory" still needs a server — it fails the primary requirement (L2).

### ADR-2 (L4) — Use `pyoxigraph` in-memory `Store` for in-memory mode

**Context.** In-memory mode must compute `N−O`/`O−N` across named graphs with the same semantics as
the remote SPARQL path, fast, no server.

**Considered options.**
1. **`pyoxigraph` in-memory `Store` + SPARQL Update.**
2. Pure `rdflib` Python set-difference (`graph_n - graph_o`).
3. `rdflib` SPARQL Update engine.
4. `oxrdflib` (oxigraph as rdflib Store backend).

**Decision:** Option 1, with Option 2 kept as a lightweight reference fallback behind the same port.

**Consequences.** + Identical SPARQL `MINUS`/named-graph/`FILTER` semantics as remote → logic and
tests transfer 1:1; + 10⁵–10⁶ triples comfortably, ~tens of ms; + same `Store` switches to
RocksDB-on-disk if RAM-bound; − native binary dependency (`pyoxigraph` wheels); − no in-process Graph
Store Protocol (irrelevant in-memory — we load programmatically).

**Pros and cons.**
- *Option 1:* Good, because semantics match remote exactly. Good, because fastest at scale. Bad, because native dep.
- *Option 2:* Good, because zero native deps, trivial code. Bad, because rdflib set-ops are **not** isomorphism-aware — blank nodes from independently-parsed files compare unequal, producing spurious diffs; viable only because our default policy excludes blank nodes. Bad, because pure-Python slow at scale.
- *Option 3:* Good, because SPARQL expressiveness. Bad, because rdflib's pure-Python engine is the slowest SPARQL option.
- *Option 4:* Bad, because oxrdflib's SPARQL **update** falls back to rdflib on `Graph`/`ConjunctiveGraph` (the exact hot path), plus no transactions — an abstraction over pyoxigraph without the update win.

### ADR-3 (L3) — Remote mode keeps GSP + SPARQL Update, reusing existing transport

**Context.** Production runs on Fuseki; the four-graph contract feeds `diff-query-generator` queries
and the report builder and must not change.

**Decision.** Remote adapter uploads version files via **SPARQL 1.1 Graph Store Protocol** `PUT`
(replacing curl), and runs the same `CLEAR`/`INSERT … MINUS` updates via SPARQL 1.1 Update over HTTP,
reusing `requests`/`SPARQLWrapper`. The compatibility guarantee is scoped to the **named-graph
contract** consumed by dqgen and the existing description/count queries: the version, insertions,
deletions, and version-history graphs plus their `sd:NamedGraph`/`sd:name` descriptions, and the
`dsv:`/`skos-history:` typing discovered by `QUERY_DATASET_DESCRIPTION` (`adapters/__init__.py:23-66`).
It is **not** a byte-for-byte guarantee of every metadata triple.

**Note on record IRIs.** This module follows the `delta_graphs_loading_and_computation_spec.md`
convention `{base}/record/{id}` (with a slash), which differs from the script's slash-less
`${BASEURI}record/$id`. This is safe because the existing description query discovers records by
**type/property** (`?vhr dsv:hasVersionHistorySet ?vhs`), never by record-IRI shape — so dqgen and the
report builder are unaffected.

**Consequences.** + Drop-in for the current Celery path; + dqgen queries unaffected; − the remote
adapter needs a Graph Store Protocol `/data` endpoint helper that the current `FusekiDiffAdapter`
lacks (added in Task 10).

### ADR-4 (L2) — Module boundary stops at the four named graphs

**Context.** Avoid scope creep into change-category reporting (owned by dqgen + report builder).

**Decision.** This module produces version graphs, insertions/deletions graphs, and the
version-history graph (+ `sd:NamedGraph` descriptions). It computes triple-level deltas only.
Higher-level categories stay in dqgen-generated queries.

**Consequences.** + Clear ownership; + independent evolution; − consumers still depend on the exact
graph IRIs/types this module emits (treated as a published contract, validated in Task 9 tests).

### ADR-5 (L4) — Blank-node policy is configurable; default excludes blank nodes

**Decision.** A `BlankNodePolicy` enum: `EXCLUDE` (default — `isIRI(?s)` and
`isIRI||isLiteral||isNumeric(?o)`, matching the script), `SKOLEMISE` (future), `DOCUMENT_ONLY` (no
filter, caller accepts bnode noise). Encodes spec §7.2 as an explicit, testable choice rather than a
hard-coded filter.

---

## File Structure

New module rooted at `rdf_differ/` following the existing layers. **No `models/` package exists today**
(domain lives in `rdf_differ/domain/`); new pure value objects go under `rdf_differ/domain/loading/`.

| Path | Responsibility |
|------|----------------|
| `rdf_differ/domain/loading/config.py` | `VersionSpec`, `VersionStoreConfig`, `LoadMode`, `BlankNodePolicy`; validation |
| `rdf_differ/domain/loading/uris.py` | `UriBuilder` — all IRI construction (mirrors script `:317-342`) |
| `rdf_differ/domain/loading/delta_pairs.py` | `consecutive_pairs`, `direct_to_current_pairs`, `all_delta_pairs` |
| `rdf_differ/adapters/loading/graph_store_port.py` | `GraphStorePort` Protocol/ABC; `GraphStoreError` |
| `rdf_differ/adapters/loading/queries.py` | SPARQL template constants + `GraphRole`/prefixes (no free strings) |
| `rdf_differ/adapters/loading/in_memory_store.py` | `PyoxigraphInMemoryStore(GraphStorePort)` |
| `rdf_differ/adapters/loading/remote_store.py` | `RemoteSparqlStore(GraphStorePort)` (GSP + Update) |
| `rdf_differ/services/loading/loader.py` | `VersionStoreLoader` — orchestration |
| `rdf_differ/services/loading/validation.py` | structural + content validation (spec §10) |
| `rdf_differ/entrypoints/cli/load.py` | `click` CLI (in-memory + remote) |
| `tests/unit/loading/…` | unit tests per layer |
| `tests/features/rdf_loading_module.feature` | BDD (shipped by this Epic) |
| `tests/steps/test_rdf_loading_module.py` | step defs |
| `.importlinter` | layer + store-seam contracts (new) |
| `requirements/common.txt` | add `pyoxigraph` |

Retired at Task 10: `resources/load_versions.sh`, the subprocess path in
`rdf_differ/adapters/skos_history_wrapper.py:192-213`.

---

## Migration & Cutover

1. Build the new module behind the port (Tasks 1–8) without touching the live path.
2. Rewire `FusekiDiffAdapter.create_diff` (`diff_adapter.py:146-168`) to call `VersionStoreLoader`
   with `RemoteSparqlStore` instead of `SKOSHistoryRunner().run()` (Task 9).
3. Verify the four-graph contract via parity tests (T6) and the existing description/count queries
   (`__init__.py:23-118`).
4. Delete `load_versions.sh` and the subprocess code; adapt the old BDD features
   `prepare_config.feature` / `execute_skos_history.feature` (Task 10).

---

## Self-Review

- **Feature → task coverage (F1–F15):**

  | Feature | Task(s) | Feature | Task(s) |
  |---------|---------|---------|---------|
  | F1 config | 1 | F9 delta MINUS | 4 (`delta_update`), 5/7 |
  | F2 GSP PUT | 6 | F10 bnode filter | 4 (`BLANK_NODE_FILTERS`), ADR-5 |
  | F3 BASEURI | 2 (`UriBuilder`) | F11 delta metadata | 4 (`delta_metadata_update`), 7 |
  | F4 service desc | 4 (`service_description_update`), 7 | F12 two-pass order | 7 (asserted in test) |
  | F5 history set | 4 (`history_set_update`), 7 | F13 delta pairs | 3 |
  | F6 version record | 4 (`version_record_update`), 7 | F14 date hacks→config | 1 (`resolve_version_meta`) |
  | F7 id/date resolution | 1 (`resolve_version_meta`), 7 | F15 sd:namedGraph reg | 4 (`register_named_graph_update`), 7 |
  | F8 xhv:prev | 4 (`prev_link_update`), 7 | | |

- **Limitation → remediation:** L1→all (Python+tests); L2→Tasks 5/9; L3→Task 10 (delete subprocess);
  L4→Task 4 (templated, bound); L5→Tasks 5/7 (CLEAR before INSERT, asserted); L6/L7→Task 1
  (`BlankNodePolicy` guard, `resolve_version_meta`); L8→Task 8; L9→Task 3; L10→Task 4/7 (explicit
  metadata graph).
- **EPIC task (1–9) → plan task (1–10):** EPIC 1→1–3; 2→4; 3→5; 4→6; 5→7; 6→8; 7→9; 8→10; 9→10
  (`.importlinter`). The plan splits EPIC Task 1 (domain models) across plan Tasks 1–3.
- **Type consistency:** `GraphStorePort` method names (`load_graph`, `run_update`, `ask`,
  `count_graph`, `serialize_graph`, `clear_graph`) are identical across Tasks 4–10;
  `delta_update`/`clear_graph` query helpers used consistently; `VersionStoreConfig.validate()`
  returns self everywhere.
- **Placeholder scan:** Tasks 7–9 describe Step 3 orchestration in prose, but every write now binds
  to a **named template builder defined in Task 4 Step 3b** (`service_description_update`,
  `history_set_update`, `version_record_update`, `prev_link_update`, `delta_metadata_update`,
  `register_named_graph_update`) with its own failing test, so F4–F8/F11/F15 each have an executable
  target. Tasks 1–6 carry complete code.

> Full task-by-task code (failing tests + minimal implementations) is preserved verbatim in
> `inputs/IMPLEMENTATION-PLAN-rdf-loading-module.md`; `tasks.md` is the checklist view.
