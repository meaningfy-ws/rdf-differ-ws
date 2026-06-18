# Design — RDF Loading Module

> Derived from EPIC "Rewrite the SKOS-History version-loading & delta-computation script in Python"
> (this change's `proposal.md`). This is the decisions/"how" half of the PLAN; the executable task
> breakdown is in `tasks.md`. The original EPIC/PLAN that seeded this change are **superseded** by
> `proposal.md` + this `design.md` + `tasks.md`; the unique reference seeds (deep delta spec,
> synthesis, Gherkin, seed brief) remain under `inputs/`. This design records the **final agreed
> decisions**, marking where they **override** the legacy ADRs.

**Goal:** Replace `resources/load_versions.sh` (run via subprocess from `skos_history_wrapper.py`)
with a layered, fully-tested Python RDF Loading Module that loads RDF versions and computes
skos-history delta graphs in **three config-selected modes** behind one port — remote (any SPARQL 1.1
endpoint via HTTP) and two in-memory engines (pyoxigraph, rdflib) — and, in the same epic, dissolve
`rdf_differ/utils/`, tighten import-linter package-wide, and migrate the domain models to pydantic.

**Architecture:** A single secondary-adapter port, `GraphStorePort` (`put_graph`, `clear_graph`,
`update`, `query`, `serialize`), isolates all triple-store interaction. The loading **service**
depends only on that port and on SPARQL template **constants**, so the identical delta logic runs
against `RemoteSparqlStore`, `PyoxigraphStore`, or `RdflibStore`, chosen by dependency injection from
config/flag (`remote|oxigraph|rdflib`). Domain models (config, URI builder, delta-pair math,
blank-node policy) are **pydantic v2** value objects with validators and carry no I/O-framework
dependency. A new CLI entrypoint and the existing API/Celery path both wire any of the three engines;
the in-memory full report depends on an external eds4jinja2 enhancement with a remote-only fallback.

**Tech Stack:** Python 3.12+, `pyoxigraph` (new, in-memory engine), `rdflib` (already present, second
in-memory engine + parsing), `requests` + `SPARQLWrapper` (already present, remote transport),
`click` (CLI, already present), **pydantic v2** + **pydantic-settings** (config/value objects/domain
migration — DEC-3; `StoreSettings` env binding — DEC-10), `eds4jinja2` (external; in-memory report
path only, via its upstream enhancement), `pytest` + `pytest-bdd` (tests), `import-linter`
(already present from the modernization; this epic **tightens** its contracts — DEC-8).

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

### ADR-2 (L4) — **OVERRIDDEN by DEC-2** — Two config-selected in-memory engines (pyoxigraph **and** rdflib)

> **This ADR is OVERRIDDEN.** The legacy ADR-2 chose `pyoxigraph` only, keeping rdflib merely as a
> "reference fallback". The final decision (**DEC-2**) makes **both** first-class, config-selected
> implementations of `GraphStorePort` (`PyoxigraphStore`, `RdflibStore`), alongside `RemoteSparqlStore`.
> The pros/cons below are retained for context; the conclusion is superseded.

**Context.** In-memory mode must compute `N−O`/`O−N` across named graphs with the same semantics as
the remote SPARQL path, fast, no server.

**Considered options.**
1. **`pyoxigraph` in-memory `Store` + SPARQL Update.**
2. Pure `rdflib` Python set-difference (`graph_n - graph_o`).
3. `rdflib` SPARQL Update engine.
4. `oxrdflib` (oxigraph as rdflib Store backend).

**Legacy decision (superseded):** Option 1 only, Option 2 as fallback. **Final decision (DEC-2):**
ship **both** Option 1 (`PyoxigraphStore`, fast, native) and Option 3/2 (`RdflibStore`,
dependency-light, pure-Python) as peer adapters chosen by `engine`. See DEC-2.

**Pros and cons.**
- *Option 1:* Good, because semantics match remote exactly and it is fastest at scale. Bad, because native dep.
- *Option 2:* Good, because zero native deps, trivial code. Bad, because rdflib set-ops are **not** isomorphism-aware — blank nodes from independently-parsed files compare unequal, producing spurious diffs; viable only because our default policy excludes blank nodes. Bad, because pure-Python slow at scale.
- *Option 3:* Good, because SPARQL expressiveness keeps the templates engine-agnostic. Bad, because rdflib's pure-Python engine is the slowest SPARQL option.
- *Option 4:* Bad, because oxrdflib's SPARQL **update** falls back to rdflib on `Graph`/`ConjunctiveGraph` (the exact hot path), plus no transactions — an abstraction over pyoxigraph without the update win.

### ADR-3 (L3) — Remote mode keeps GSP + SPARQL Update, reusing existing transport

**Context.** Production runs on Fuseki; the four-graph contract feeds `diff-query-generator` queries
and the report builder and must not change.

**Decision.** `RemoteSparqlStore` targets **any SPARQL 1.1 endpoint** (Fuseki today, but
**not Fuseki-specific**): it uploads version files via **SPARQL 1.1 Graph Store Protocol** `PUT`
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
lacks (added at the remote-mode cutover, Task 13).

### ADR-4 (L2) — Module boundary stops at the four named graphs

**Context.** Avoid scope creep into change-category reporting (owned by dqgen + report builder).

**Decision.** This module produces version graphs, insertions/deletions graphs, and the
version-history graph (+ `sd:NamedGraph` descriptions). It computes triple-level deltas only.
Higher-level categories stay in dqgen-generated queries.

**Consequences.** + Clear ownership; + independent evolution; − consumers still depend on the exact
graph IRIs/types this module emits (treated as a published contract, validated by the parity tests at
the remote-mode cutover, Task 13).

### ADR-5 (L4) — Blank-node policy is configurable; default excludes blank nodes

**Decision.** A `BlankNodePolicy` enum: `EXCLUDE` (default — `isIRI(?s)` and
`isIRI||isLiteral||isNumeric(?o)`, matching the script), `SKOLEMISE` (**now SUPPORTED — see DEC-9,
which overrides this "future" note**), `DOCUMENT_ONLY` (no filter, caller accepts bnode noise).
Encodes spec §7.2 as an explicit, testable choice rather than a hard-coded filter.

---

## Final agreed decisions (override the legacy ADRs where noted)

These are the decisions the developer must **not** relitigate. They supersede the conflicting legacy
ADRs above; the override is stated explicitly so the golden thread from the original shaping is intact.

### DEC-1 — Scope: one epic = loading module + utils dissolution + stricter import-linter + pydantic domain migration

**Decision.** This epic is **not** scoped to the loading module alone. It additionally (a) fully
dissolves `rdf_differ/utils/` (see the dissolution map below), (b) tightens import-linter
package-wide, and (c) migrates the existing hand-written `rdf_differ/domain/model.py` (`Dataset`,
`DatasetVersion`, `VersionsDelta`) to pydantic. **NO FastAPI** (Flask/Connexion stays; UI unchanged).
**NO LinkML** (no code generation; models are hand-written). Bundling these makes the loading module
land into a clean, contract-enforced package rather than fighting the legacy one.

### DEC-2 — Storage: one `GraphStorePort`, three config-selected implementations **(OVERRIDES ADR-2)**

**Decision.** A single `GraphStorePort` with **three** implementations, backend chosen by config:
`RemoteSparqlStore` (any SPARQL 1.1 endpoint incl. Fuseki — GSP `PUT` + SPARQL Update/Query over
HTTP), `PyoxigraphStore` (in-memory), `RdflibStore` (in-memory). **This overrides legacy ADR-2**,
which chose pyoxigraph only with rdflib as a non-shipping fallback; now **both** in-memory engines are
first-class, selected by `engine` (`remote|oxigraph|rdflib`). Services depend only on
`GraphStorePort` (DIP) and never import `pyoxigraph`/`rdflib`/`requests`/`SPARQLWrapper` directly.

**Why both engines:** `pyoxigraph` is fast and native but adds a binary wheel; `rdflib` is already a
dependency and gives a dependency-light, pure-Python engine for constrained/CI environments. Keeping
the port engine-agnostic (SPARQL templates, not native set-ops) is what makes the third engine cheap.

### DEC-3 — Models: pydantic v2, hand-written **(OVERRIDES legacy Task-1 frozen-dataclasses choice)**

**Decision.** Config and value objects are **pydantic v2** with validators, **not** frozen
dataclasses. **This overrides** the legacy PLAN Task-1/ADR that chose frozen dataclasses. New
`VersionStoreConfig` + value objects validate: ≥2 versions, absolute IRIs (scheme/base), and that
version files exist. The existing `rdf_differ/domain/model.py` is also **migrated to pydantic** in
this epic.

**Layering note.** Per the Meaningfy norm, **pydantic is ALLOWED in the `domain` layer**. The `domain`
layer still MUST NOT import I/O frameworks (flask, connexion, celery, click, requests, rdflib,
pyoxigraph, eds4jinja2) — enforced by import-linter (see contracts below).

### DEC-4 — Remote mode is the always-ships core

**Decision.** `RemoteSparqlStore` is the faithful Python replacement for `resources/load_versions.sh`
loading into a SPARQL endpoint, preserving the four-named-graph + version-history contract so dqgen
queries and the report builder keep working unchanged.

**Implemented cutover (safe, flag-gated).** The Celery `create_diff` task selects the diff engine on
the `RDF_DIFFER_USE_PYTHON_LOADER` flag: when **on**, it builds a per-dataset `RemoteSparqlStore`
(GSP `…/{ds}/data`, update `…/{ds}`, query `…/{ds}/query`) and runs `VersionStoreLoader` via the pure
`services.loading.diff_service`; when **off (default)** it keeps the legacy subprocess. This makes the
Python loader the production path *selectable and verifiable* without a big-bang deletion. **Physical
retirement** of `load_versions.sh` + `skos_history_wrapper` is the final step, gated on a Fuseki
parity smoke test (`make start-services-test` + flip the flag) — deferred because it can only be
validated against a live endpoint, and the relevant tests are environmental.

### DEC-5 — In-memory has two deliverables split at a clean seam; the full report is an external dependency

**Decision.** The in-memory side splits cleanly:

1. **In-memory diff artifacts** — the four named graphs serialisable to files + insertion/deletion
   counts + validation. **No external dependency**; lands with the core.
2. **In-memory full report** — depends on an **external, separately-shipped eds4jinja2 enhancement**,
   authored as its own epic in the eds4jinja2 repo and implemented in a different thread. **Mechanism:**
   eds4jinja2 will gain `ReportBuilder(external_data_source_builders=…)` plus an engine-agnostic
   `InMemorySPARQLDataSource`; rdf-differ overrides `from_endpoint` to query the in-process store
   (templates untouched).

**Stated as a dependency with graceful fallback.** If the eds4jinja2 enhancement is **not present**,
in-memory reporting degrades to **remote-only** with **NO rework of the core**. The diff-artifacts
deliverable is unaffected by the eds4jinja2 release.

**eds4jinja2 findings (why the enhancement is required).** Investigation of the current eds4jinja2:
it ships **NO SPARQL server**; its `ReportBuilder` is **hardwired to `build_eds_environment`** with
default builders (**no injection** seam); its only local source `from_rdf_file` / `RDFFileDataSource`
is **file-path-only**, **re-parses per query**, and its `_fetch_tree` **raises** (tabular only). Hence
an in-process, engine-agnostic SPARQL data source plus a builder-injection seam must be added upstream
— it cannot be done from rdf-differ without forking, which DEC is a no-go.

### DEC-6 — Exposure: CLI + API/Celery, both engine-parameterised

**Decision.** Expose loading through a **Click CLI**
(`rdf-diff load --config x.yaml --engine remote|oxigraph|rdflib [--report]`) **and** the existing API
create-diff endpoint, which gains an `engine`/`mode` parameter and runs async over the existing
**Celery + Redis** channel (status + the revoke/cancel queue in `adapters/redis.py`). For in-memory
tasks the worker builds the store (and, for reports, the eds4jinja2 in-memory wiring) **inside the
worker for the task lifetime**.

### DEC-7 — `rdf_differ/utils/` dissolution map

`rdf_differ/utils/` is removed; its members move to the correct layer:

| Legacy `utils/` member | Lands in | Layer |
|------------------------|----------|-------|
| `file_utils` filesystem ops (`dir_exists`, `save_files`, `empty_directory`, `copy_file_to_destination`, `list_*_from_path`, …) | a new `adapters` filesystem module | adapters |
| `INPUT_MIME_TYPES` | domain constants | domain |
| `check_dataset_name_validity`, `build_unique_name`, `build_secure_filename` | domain | domain |
| `build_dataset_reports_location`, `read_meta_file` | services (report) | services |
| `rdf_converter` | adapters (RDF I/O) | adapters |
| `conversions.strtobool` | a config helper | config/helper |

Then **remove `rdf_differ/utils/`** and drop its **two** import-linter contracts. **Consumers to
update** include `tests/steps/*.py` and `services/report_handling.py` imports (and any other importer
of `rdf_differ.utils`).

### DEC-8 — Stricter import-linter contracts

Beyond keeping the layers contract (now **without** `utils`), add:

- **Layers contract (updated):** `entrypoints > services > adapters > domain` (utils removed).
- **Forbidden — services store/report seam (DIP):** `rdf_differ.services.loading` MUST NOT import
  `pyoxigraph`, `rdflib`, `requests`, `SPARQLWrapper`, `eds4jinja2`. (Scoped to the **new** loading
  service module: it is the code that must obey DIP. The legacy services — `report_handling` uses
  `eds4jinja2`, `queue` injects `requests` — predate this and are addressed in a follow-up; widening
  the contract package-wide is deferred so it does not block this epic.)
- **Forbidden — domain purity:** `rdf_differ.domain` MUST NOT import I/O frameworks (`flask`,
  `connexion`, `celery`, `click`, `requests`, `rdflib`, `pyoxigraph`, `eds4jinja2`). (pydantic is
  allowed.)
- **Independence — store adapters:** the three store adapter modules (`remote_store`,
  `in_memory_oxigraph_store`, `in_memory_rdflib_store`) MUST NOT import each other.

### DEC-9 — Blank-node `SKOLEMISE` is a supported, pluggable, deterministic option **(OVERRIDES ADR-5)**

**Decision.** `BlankNodePolicy.SKOLEMISE` is **supported now**, not reserved. Blank-node handling is a
pluggable **`BlankNodeStrategy`** seam (Strategy pattern / OCP) so the algorithm can be improved later
without an API change. Three behaviours:

- `EXCLUDE` (default) and `DOCUMENT_ONLY` remain **SPARQL-filter choices** in the delta query
  templates (`isIRI` filter present / absent) — no graph rewrite.
- `SKOLEMISE` is a **transform on the parsed RDF before load** (engine-agnostic — applied at the load
  boundary for both in-memory and remote modes), so the four-named-graph delta logic above it is
  unchanged.

**Initial KISS implementation — deterministic, W3C-compliant, no new dependency** (uses **rdflib** end
to end):
1. `rdflib.compare.to_canonical_graph(g)` → **deterministic** canonical blank-node labels (stable
   across runs and parse order);
2. `Graph.skolemize(authority=<dataset base IRI>, basepath="/.well-known/genid/")` → **W3C RDF 1.1
   Skolem IRIs** of the form `{base}/.well-known/genid/{label}`, reversible via `de_skolemize()`.

Deliberately simple; a richer canonicalisation (e.g. full URDNA2015, cross-version stable identity) is
a **later improvement behind the same `BlankNodeStrategy` interface** — the seam exists from day one.

**Layering.** The `BlankNodeStrategy` **interface** and the `BlankNodePolicy` enum live in `domain`
(pure). The rdflib-backed `SKOLEMISE` transform lives in **`adapters`** (RDF I/O) because it imports
`rdflib`, which DEC-8 forbids in `domain`.

### DEC-10 — Store connection is a typed settings concern, separate from dataset config

**Decision.** Cleanly separate two concerns the legacy script conflated:

- **`VersionStoreConfig`** (pydantic, from YAML) describes the **dataset/diff shape** only — versions,
  IRIs, `engine`, blank-node policy. Portable, environment-independent; it carries **no endpoint or
  credentials**.
- **`StoreSettings`** (pydantic-settings `BaseSettings`, env `RDF_DIFFER_*`) describes the **remote
  store connection** — base endpoint, GSP `/data`, update/query paths, credentials, timeouts/retries.
  In-memory engines ignore it.

A **`build_graph_store(engine, settings) -> GraphStorePort`** factory at the composition root selects
and constructs the adapter, used **identically by the CLI and the API/Celery path**. The CLI may
override individual settings (e.g. `--endpoint`), but the environment is canonical (12-factor).
`RemoteSparqlStore` receives its connection via injected `StoreSettings` and **never reads env
itself**. This keeps `services` pure (DIP), the YAML portable, and connection config consistent across
all entrypoints.

**Layering.** `StoreSettings` (reads env = I/O) and the factory live in **`adapters`/composition
root**, never in `domain`.

---

## `GraphStorePort` interface

The single secondary-adapter port. Engine-agnostic; all three adapters implement it identically.

| Method | Purpose |
|--------|---------|
| `put_graph(graph_iri, data, content_type)` | Replace a named graph's contents (GSP `PUT` semantics / programmatic bulk-load in memory). Idempotent. |
| `clear_graph(graph_iri)` | Empty a named graph (`CLEAR GRAPH`) before recompute (L5 idempotency). |
| `update(sparql_update)` | Run a SPARQL 1.1 Update (the `CLEAR`/`INSERT … MINUS` delta writes + metadata writes), bound from named template constants. |
| `query(sparql_query)` | Run a SPARQL 1.1 Query/`ASK`/`COUNT` (delta counts, validation checks). |
| `serialize(graph_iri, content_type)` | Export a named graph as RDF (the in-memory diff artifacts written to files). |

Services depend only on this port; concrete adapters translate transport/engine errors to
`GraphStoreError`.

---

## eds4jinja2 dependency & fallback

The **in-memory full report** is the only part of this epic that depends on external work. The
dependency, mechanism, findings, and fallback are recorded in **DEC-5**. In short: rdf-differ
**depends on** an eds4jinja2 release that adds builder injection + an in-process
`InMemorySPARQLDataSource`; rdf-differ overrides `from_endpoint` to query the in-process store with
templates untouched. **Fallback:** if that release is absent, `--report` in an in-memory engine either
errors clearly with guidance to use `--engine remote`, or (per CLI design) falls back to remote-only;
either way the **core and the in-memory diff-artifacts deliverable are unaffected**. The corresponding
upstream work is shaped separately under `openspec/changes/eds4jinja2-upstream-fix/` (different repo
/ thread); this epic does **not** build it.

---

## File Structure

New module rooted at `rdf_differ/` following the existing layers. **No `models/` package exists today**
(domain lives in `rdf_differ/domain/`); new pydantic value objects go under `rdf_differ/domain/loading/`.

| Path | Responsibility |
|------|----------------|
| `rdf_differ/domain/loading/config.py` | `VersionSpec`, `VersionStoreConfig`, `LoadMode`/`Engine`, `BlankNodePolicy`; **pydantic v2** validators (≥2 versions, absolute IRIs, files exist) |
| `rdf_differ/domain/loading/uris.py` | `UriBuilder` — all IRI construction (mirrors script `:317-342`) |
| `rdf_differ/domain/loading/delta_pairs.py` | `consecutive_pairs`, `direct_to_current_pairs`, `all_delta_pairs` |
| `rdf_differ/domain/constants.py` | `INPUT_MIME_TYPES`, graph-role/MIME constants (from `utils`, DEC-7) |
| `rdf_differ/domain/model.py` | existing `Dataset`/`DatasetVersion`/`VersionsDelta` **migrated to pydantic** (DEC-3) |
| `rdf_differ/adapters/loading/graph_store_port.py` | `GraphStorePort` Protocol/ABC (`put_graph`, `clear_graph`, `update`, `query`, `serialize`); `GraphStoreError` |
| `rdf_differ/adapters/loading/queries.py` | SPARQL template constants + `GraphRole`/prefixes (no free strings); `EXCLUDE`/`DOCUMENT_ONLY` bnode filters (DEC-9) |
| `rdf_differ/domain/loading/blank_nodes.py` | `BlankNodeStrategy` interface + `BlankNodePolicy` (pure; DEC-9) |
| `rdf_differ/adapters/loading/skolemizer.py` | rdflib `SKOLEMISE` transform — `to_canonical_graph` + `skolemize(.well-known/genid)` (DEC-9) |
| `rdf_differ/adapters/loading/in_memory_oxigraph_store.py` | `PyoxigraphStore(GraphStorePort)` |
| `rdf_differ/adapters/loading/in_memory_rdflib_store.py` | `RdflibStore(GraphStorePort)` |
| `rdf_differ/adapters/loading/remote_store.py` | `RemoteSparqlStore(GraphStorePort)` (GSP `PUT` + Update/Query; any SPARQL 1.1 endpoint; takes injected `StoreSettings`) |
| `rdf_differ/adapters/loading/settings.py` | `StoreSettings` (pydantic-settings, env `RDF_DIFFER_*`) — remote connection (DEC-10) |
| `rdf_differ/adapters/loading/store_factory.py` | `build_graph_store(engine, settings)` → `GraphStorePort` (composition-root helper; DEC-10) |
| `rdf_differ/adapters/filesystem.py` | filesystem ops from `utils/file_utils` + `rdf_converter` RDF I/O (DEC-7) |
| `rdf_differ/services/loading/loader.py` | `VersionStoreLoader` — orchestration |
| `rdf_differ/services/loading/validation.py` | structural + content validation (spec §10) |
| `rdf_differ/services/loading/artifacts.py` | in-memory diff-artifact output (serialise four graphs + counts) |
| `rdf_differ/services/loading/report.py` | **[gated]** in-memory full report via eds4jinja2 enhancement + remote-only fallback (DEC-5) |
| `rdf_differ/entrypoints/cli/load.py` | `click` CLI (`--engine remote|oxigraph|rdflib [--report]`) |
| `rdf_differ/entrypoints/.../create_diff` | existing API endpoint gains `engine`/`mode` param; async via Celery+Redis (DEC-6) |
| `tests/unit/loading/…` | unit tests per layer |
| `tests/features/rdf_loading_module.feature` | BDD (shipped by this Epic) |
| `tests/steps/test_rdf_loading_module.py` | step defs |
| `.importlinter` | layers + store-seam + domain-purity + adapter-independence contracts (DEC-8); utils contracts removed |
| `requirements/common.txt` | add `pyoxigraph` (`rdflib` already present) |

Retired at cutover: `resources/load_versions.sh`, the subprocess path in
`rdf_differ/adapters/skos_history_wrapper.py:192-213`. Removed entirely: `rdf_differ/utils/` (DEC-7).

---

## Migration & Cutover

1. Build the new module behind the port (domain models+config → URIs/delta math → port+templates →
   the three store adapters → loader → validation → artifacts → CLI) without touching the live path.
2. Wire the API/Celery path (`engine`/`mode` param; in-memory store built inside the worker, DEC-6).
3. **Remote-mode cutover (DEC-4):** rewire `FusekiDiffAdapter.create_diff` (`diff_adapter.py:146-168`)
   to call `VersionStoreLoader` with `RemoteSparqlStore` instead of `SKOSHistoryRunner().run()`;
   verify the four-graph contract via parity tests (T6) and the existing description/count queries
   (`__init__.py:23-118`); **delete `load_versions.sh` and the subprocess code**; adapt the old BDD
   features `prepare_config.feature` / `execute_skos_history.feature`.
4. **Utils dissolution (DEC-7):** move each `utils/` member to its target layer, update all consumers
   (incl. `tests/steps/*.py`, `services/report_handling.py`), remove `rdf_differ/utils/` and its two
   import-linter contracts.
5. **Stricter import-linter (DEC-8):** add the forbidden + independence contracts; run `lint-imports`.
6. **[Gated on the eds4jinja2 epic]** wire the in-memory full report; until the eds4jinja2 release
   lands, `--report` on an in-memory engine falls back to remote-only — no core rework.

---

## Self-Review

- **Feature → task coverage (F1–F15):**

  | Feature | Task(s) | Feature | Task(s) |
  |---------|---------|---------|---------|
  | F1 config | 1 | F9 delta MINUS | 4 (`delta_update`), 5/6/8 |
  | F2 GSP PUT | 7 | F10 bnode filter | 4 (`BLANK_NODE_FILTERS`) + 4b (skolemise, DEC-9) |
  | F3 BASEURI | 2 (`UriBuilder`) | F11 delta metadata | 4 (`delta_metadata_update`), 8 |
  | F4 service desc | 4 (`service_description_update`), 8 | F12 two-pass order | 8 (asserted in test) |
  | F5 history set | 4 (`history_set_update`), 8 | F13 delta pairs | 3 |
  | F6 version record | 4 (`version_record_update`), 8 | F14 date hacks→config | 1 (`resolve_version_meta`) |
  | F7 id/date resolution | 1 (`resolve_version_meta`), 8 | F15 sd:namedGraph reg | 4 (`register_named_graph_update`), 8 |
  | F8 xhv:prev | 4 (`prev_link_update`), 8 | | |

- **Limitation → remediation:** L1→all (Python+tests); L2→in-memory engines (oxigraph+rdflib) + CLI;
  L3→remote cutover (delete subprocess); L4→templated, bound queries; L5→CLEAR before INSERT,
  asserted; L6/L7→`BlankNodePolicy` guard + config-driven `resolve_version_meta`; L8→validation
  service; L9→delta-pair math; L10→explicit metadata graph.
- **Decision coverage:** DEC-1→utils + import-linter + pydantic tasks; DEC-2→three store adapters
  (overrides ADR-2); DEC-3→pydantic config + domain migration (overrides legacy Task-1); DEC-4→remote
  cutover; DEC-5→artifacts task (ships) + gated report task (external dep, fallback); DEC-6→CLI +
  API/Celery tasks; DEC-7→utils dissolution task; DEC-8→stricter import-linter task;
  DEC-9→`BlankNodeStrategy` + skolemiser (Task 4b, overrides ADR-5); DEC-10→`StoreSettings` +
  `build_graph_store` factory (Tasks 7, 11).
- **Type consistency:** `GraphStorePort` method names (`put_graph`, `clear_graph`, `update`, `query`,
  `serialize`) are identical across all adapters and the loader; `delta_update`/`clear_graph` query
  helpers used consistently; pydantic `VersionStoreConfig` validation runs at construction.
- **Placeholder scan:** the loader (Task 8) orchestrates writes in prose, but every write binds to a
  **named template builder defined in Task 4** (`service_description_update`, `history_set_update`,
  `version_record_update`, `prev_link_update`, `delta_metadata_update`, `register_named_graph_update`)
  with its own failing test, so F4–F8/F11/F15 each have an executable target.
- **Gating clarity:** every always-ships deliverable (remote core + in-memory diff artifacts) is in
  Tasks 1–15; only Task 16 (in-memory full report) is **gated** on the external eds4jinja2 epic and
  carries the remote-only fallback (DEC-5).

> `tasks.md` is the checklist view of the per-task work, re-sequenced for the final shape; each task
> is executed test-first.
