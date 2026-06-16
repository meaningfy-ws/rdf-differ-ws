# RDF Loading Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `resources/load_versions.sh` (run via subprocess from `skos_history_wrapper.py`) with a layered, fully-tested Python RDF Loading Module that loads RDF versions and computes skos-history delta graphs in **two interchangeable modes** — in-memory (pyoxigraph, no server) and remote (Fuseki via HTTP).

**Architecture:** A single secondary-adapter port, `GraphStorePort`, isolates all triple-store interaction. The loading **service** depends only on that port and on SPARQL template **constants**, so the identical delta logic runs against either an in-memory `pyoxigraph.Store` or a remote SPARQL endpoint, chosen by dependency injection. Domain models (config, URI builder, delta-pair math, blank-node policy) carry no framework dependencies. A new CLI entrypoint exposes in-memory mode; the existing API/Celery path is rewired to the remote adapter.

**Tech Stack:** Python 3.8+, `pyoxigraph` (new), `rdflib~=7.0` (already present, parsing/fallback), `requests~=2.31` + `SPARQLWrapper~=2.0` (already present, remote transport), `click~=8.1` (CLI, already present), frozen `dataclasses` (config — decided in Task 1; not pydantic), `pytest` + `pytest-bdd` (tests), `import-linter` (new, contracts).

---

## Architectural Decision Records

These ADRs record the decisions the developer must **not** relitigate. Each weighs the real alternatives and commits.

### ADR-1 (L3) — Isolate the triple store behind a single `GraphStorePort`

**Context.** Today the store is reached three incompatible ways: `curl` in bash (`load_versions.sh`), `requests` for Fuseki admin (`diff_adapter.py`), and `SPARQLWrapper` for query/update (`sparql.py`). Dual-mode is impossible while the store access is scattered and concrete.

**Considered options.**
1. **One port, two adapters (in-memory, remote).**
2. Two parallel services (one per backend) sharing helpers.
3. Keep `SPARQLWrapper` everywhere; run a local Fuseki for "in-memory".

**Decision:** Option 1.

**Consequences.** + Same delta logic both modes; + trivially mockable services; + future backends (GraphDB, Oxigraph-server, RocksDB) are new adapters; − one abstraction layer to maintain; − port must be the lowest-common-denominator of GSP + SPARQL Update.

**Pros and cons.**
- *Option 1:* Good, because it directly enables the core dual-mode bet (DIP). Good, because services become pure and testable. Bad, because the port surface must be designed carefully.
- *Option 2:* Good, because each path is simple. Bad, because delta logic is duplicated — the exact bug-farm the rewrite must kill.
- *Option 3:* Good, because zero new code paths. Bad, because "in-memory" still needs a server — it fails the primary requirement (L2).

### ADR-2 (L4) — Use `pyoxigraph` in-memory `Store` for in-memory mode

**Context.** In-memory mode must compute `N−O`/`O−N` across named graphs with the same semantics as the remote SPARQL path, fast, no server.

**Considered options.**
1. **`pyoxigraph` in-memory `Store` + SPARQL Update.**
2. Pure `rdflib` Python set-difference (`graph_n - graph_o`).
3. `rdflib` SPARQL Update engine.
4. `oxrdflib` (oxigraph as rdflib Store backend).

**Decision:** Option 1, with Option 2 kept as a lightweight reference fallback behind the same port.

**Consequences.** + Identical SPARQL `MINUS`/named-graph/`FILTER` semantics as remote → logic and tests transfer 1:1; + 10⁵–10⁶ triples comfortably, ~tens of ms; + same `Store` switches to RocksDB-on-disk if RAM-bound; − native binary dependency (`pyoxigraph` wheels); − no in-process Graph Store Protocol (irrelevant in-memory — we load programmatically).

**Pros and cons.**
- *Option 1:* Good, because semantics match remote exactly. Good, because fastest at scale. Bad, because native dep.
- *Option 2:* Good, because zero native deps, trivial code. Bad, because rdflib set-ops are **not** isomorphism-aware — blank nodes from independently-parsed files compare unequal, producing spurious diffs; viable only because our default policy excludes blank nodes. Bad, because pure-Python slow at scale.
- *Option 3:* Good, because SPARQL expressiveness. Bad, because rdflib's pure-Python engine is the slowest SPARQL option.
- *Option 4:* Bad, because oxrdflib's SPARQL **update** falls back to rdflib on `Graph`/`ConjunctiveGraph` (the exact hot path), plus no transactions — an abstraction over pyoxigraph without the update win.

### ADR-3 (L3) — Remote mode keeps GSP + SPARQL Update, reusing existing transport

**Context.** Production runs on Fuseki; the four-graph contract feeds `diff-query-generator` queries and the report builder and must not change.

**Decision.** Remote adapter uploads version files via **SPARQL 1.1 Graph Store Protocol** `PUT` (replacing curl), and runs the same `CLEAR`/`INSERT … MINUS` updates via SPARQL 1.1 Update over HTTP, reusing `requests`/`SPARQLWrapper`. The compatibility guarantee is scoped to the **named-graph contract** consumed by dqgen and the existing description/count queries: the version, insertions, deletions, and version-history graphs plus their `sd:NamedGraph`/`sd:name` descriptions, and the `dsv:`/`skos-history:` typing discovered by `QUERY_DATASET_DESCRIPTION` (`adapters/__init__.py:23-66`). It is **not** a byte-for-byte guarantee of every metadata triple.

**Note on record IRIs.** This module follows the `delta_graphs_loading_and_computation_spec.md` convention `{base}/record/{id}` (with a slash), which differs from the script's slash-less `${BASEURI}record/$id`. This is safe because the existing description query discovers records by **type/property** (`?vhr dsv:hasVersionHistorySet ?vhs`), never by record-IRI shape — so dqgen and the report builder are unaffected.

**Consequences.** + Drop-in for the current Celery path; + dqgen queries unaffected; − the remote adapter needs a Graph Store Protocol `/data` endpoint helper that the current `FusekiDiffAdapter` lacks (added in Task 10).

### ADR-4 (L2) — Module boundary stops at the four named graphs

**Context.** Avoid scope creep into change-category reporting (owned by dqgen + report builder).

**Decision.** This module produces version graphs, insertions/deletions graphs, and the version-history graph (+ `sd:NamedGraph` descriptions). It computes triple-level deltas only. Higher-level categories stay in dqgen-generated queries.

**Consequences.** + Clear ownership; + independent evolution; − consumers still depend on the exact graph IRIs/types this module emits (treated as a published contract, validated in Task 9 tests).

### ADR-5 (L4) — Blank-node policy is configurable; default excludes blank nodes

**Decision.** A `BlankNodePolicy` enum: `EXCLUDE` (default — `isIRI(?s)` and `isIRI||isLiteral||isNumeric(?o)`, matching the script), `SKOLEMISE` (future), `DOCUMENT_ONLY` (no filter, caller accepts bnode noise). Encodes spec §7.2 as an explicit, testable choice rather than a hard-coded filter.

---

## File Structure

New module rooted at `rdf_differ/` following the existing layers. **No `models/` package exists today** (domain lives in `rdf_differ/domain/`); new pure value objects go under `rdf_differ/domain/loading/`.

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

Retired at Task 10: `resources/load_versions.sh`, the subprocess path in `rdf_differ/adapters/skos_history_wrapper.py:192-213`.

---

## Migration & Cutover

1. Build the new module behind the port (Tasks 1–8) without touching the live path.
2. Rewire `FusekiDiffAdapter.create_diff` (`diff_adapter.py:146-168`) to call `VersionStoreLoader` with `RemoteSparqlStore` instead of `SKOSHistoryRunner().run()` (Task 9).
3. Verify the four-graph contract via parity tests (T6) and the existing description/count queries (`__init__.py:23-118`).
4. Delete `load_versions.sh` and the subprocess code; adapt the old BDD features `prepare_config.feature` / `execute_skos_history.feature` (Task 10).

---
## Tasks

### Task 1: Domain config models

**Files:**
- Create: `rdf_differ/domain/loading/config.py`
- Test: `tests/unit/loading/test_config.py`

- [ ] **Step 1: Write the failing test**
```python
import pytest
from pathlib import Path
from rdf_differ.domain.loading.config import VersionStoreConfig, VersionSpec, LoadMode, BlankNodePolicy, ConfigError

def test_requires_two_versions(tmp_path):
    f = tmp_path / "v.ttl"; f.write_text("")
    with pytest.raises(ConfigError, match="at least two versions"):
        VersionStoreConfig(dataset_id="stw", scheme_uri="http://ex/stw",
                           base_version_iri="http://ex/stw/version",
                           versions=[VersionSpec(id="1", file=f)]).validate()

def test_rejects_duplicate_ids_and_missing_file(tmp_path):
    f = tmp_path / "v.ttl"; f.write_text("")
    cfg = VersionStoreConfig(dataset_id="stw", scheme_uri="http://ex/stw",
                             base_version_iri="http://ex/stw/version",
                             versions=[VersionSpec(id="1", file=f), VersionSpec(id="1", file=f)])
    with pytest.raises(ConfigError, match="unique"):
        cfg.validate()

def test_rejects_relative_iri(tmp_path):
    f = tmp_path / "v.ttl"; f.write_text("")
    cfg = VersionStoreConfig(dataset_id="stw", scheme_uri="stw",
                             base_version_iri="http://ex/stw/version",
                             versions=[VersionSpec(id="1", file=f), VersionSpec(id="2", file=f)])
    with pytest.raises(ConfigError, match="absolute IRI"):
        cfg.validate()
```

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/unit/loading/test_config.py -v` → FAIL (import error).

- [ ] **Step 3: Write minimal implementation**
```python
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

class ConfigError(ValueError): ...

class LoadMode(str, Enum):
    IN_MEMORY = "in_memory"
    REMOTE = "remote"

class BlankNodePolicy(str, Enum):
    EXCLUDE = "exclude"
    SKOLEMISE = "skolemise"
    DOCUMENT_ONLY = "document_only"

@dataclass(frozen=True)
class VersionSpec:
    id: str
    file: Path
    date: Optional[str] = None

@dataclass(frozen=True)
class VersionStoreConfig:
    dataset_id: str
    scheme_uri: str
    base_version_iri: str
    versions: List[VersionSpec]
    mode: LoadMode = LoadMode.IN_MEMORY
    blank_node_policy: BlankNodePolicy = BlankNodePolicy.EXCLUDE
    compute_direct_to_current: bool = True

    def validate(self) -> "VersionStoreConfig":
        if len(self.versions) < 2:
            raise ConfigError("at least two versions are required to compute deltas")
        ids = [v.id for v in self.versions]
        if len(set(ids)) != len(ids):
            raise ConfigError("version identifiers must be unique")
        for uri in (self.scheme_uri, self.base_version_iri):
            if not uri.startswith(("http://", "https://")):
                raise ConfigError(f"'{uri}' must be an absolute IRI")
        for v in self.versions:
            if not Path(v.file).is_file():
                raise ConfigError(f"version file does not exist: {v.file}")
        if self.blank_node_policy is BlankNodePolicy.SKOLEMISE:
            raise ConfigError("SKOLEMISE policy is reserved for a future release and not yet supported")
        return self
```
Add a sixth test asserting `BlankNodePolicy.SKOLEMISE` raises `ConfigError("not yet supported")` — this enforces ADR-5's "future" status instead of silently behaving like `DOCUMENT_ONLY`.

- [ ] **Step 3b: version identifier/date resolution (F7, F14)** — add to the same module:
```python
@dataclass(frozen=True)
class ResolvedVersionMeta:
    version_id: str
    identifier: str   # from data (owl:versionInfo / dcterms:hasVersion) or falls back to version_id
    date: Optional[str]  # ISO yyyy-mm-dd from data (dcterms:issued/modified) or config; None if neither

def resolve_version_meta(spec: VersionSpec, identifier_from_data: Optional[str],
                         date_from_data: Optional[str]) -> ResolvedVersionMeta:
    """Config-driven replacement for the script's owl:versionInfo/dcterms hacks and the
    'agrovoc jel' VERSION_DATE_MISSING special case (load_versions.sh:142-199, L7/F14)."""
    identifier = identifier_from_data or spec.id
    date = date_from_data or spec.date  # config date wins as fallback; no dataset names in code
    return ResolvedVersionMeta(version_id=spec.id, identifier=identifier, date=date)
```
The loader (Task 7) passes `identifier_from_data`/`date_from_data` obtained from a small `ASK`/`SELECT` over the loaded version graph; when both are absent the value is omitted, never a dataset-specific branch. Add a unit test covering: data present → data wins; data absent + config present → config; both absent → identifier falls back to id, date is `None`.

- [ ] **Step 4: Run tests to verify they pass** — `pytest tests/unit/loading/test_config.py -v` → PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(loading): typed version-store config model"`

---

### Task 2: UriBuilder

**Files:**
- Create: `rdf_differ/domain/loading/uris.py`
- Test: `tests/unit/loading/test_uris.py`

- [ ] **Step 1: Write the failing test**
```python
from rdf_differ.domain.loading.uris import UriBuilder

def test_builds_skos_history_iris():
    u = UriBuilder("http://zbw.eu/stw/version")
    assert u.history_graph() == "http://zbw.eu/stw/version"
    assert u.version_graph("9.0") == "http://zbw.eu/stw/version/9.0"
    assert u.version_record("9.0") == "http://zbw.eu/stw/version/record/9.0"
    assert u.delta("8.14", "9.0") == "http://zbw.eu/stw/version/8.14/delta/9.0"
    assert u.delta_graph("8.14", "9.0", "insertions") == "http://zbw.eu/stw/version/8.14/delta/9.0/insertions"

def test_percent_encodes_unsafe_ids():
    u = UriBuilder("http://ex/version")
    assert u.version_graph("v 1/2") == "http://ex/version/v%201%2F2"

def test_strips_trailing_slash():
    assert UriBuilder("http://ex/version/").history_graph() == "http://ex/version"
```

- [ ] **Step 2: Run to verify fail** → FAIL.
- [ ] **Step 3: Implement** (mirrors `load_versions.sh:317-342`)
```python
from urllib.parse import quote

class UriBuilder:
    def __init__(self, base_version_iri: str):
        self.base = base_version_iri.rstrip("/")
    def _slug(self, vid: str) -> str: return quote(vid, safe="")
    def history_graph(self) -> str: return self.base
    def version_record(self, vid): return f"{self.base}/record/{self._slug(vid)}"
    def version_graph(self, vid): return f"{self.base}/{self._slug(vid)}"
    def version_graph_desc(self, vid): return f"{self.version_graph(vid)}/ng"
    def delta(self, old, new): return f"{self.base}/{self._slug(old)}/delta/{self._slug(new)}"
    def delta_graph(self, old, new, op):
        assert op in {"insertions", "deletions"}
        return f"{self.delta(old, new)}/{op}"
    def delta_graph_desc(self, old, new, op): return f"{self.delta_graph(old, new, op)}/ng"
    def service_iri(self): return f"{self.base}/sparql-service"
    def service_dataset_iri(self): return f"{self.base}/sparql-service/dd"
```
- [ ] **Step 4: Run → PASS.**
- [ ] **Step 5: Commit** — `git commit -m "feat(loading): UriBuilder for skos-history IRIs"`

---

### Task 3: Delta-pair math

**Files:**
- Create: `rdf_differ/domain/loading/delta_pairs.py`
- Test: `tests/unit/loading/test_delta_pairs.py`

- [ ] **Step 1: Failing test**
```python
from rdf_differ.domain.loading.delta_pairs import all_delta_pairs

def test_two_versions_single_pair():
    assert all_delta_pairs(["8.14", "9.0"], compute_direct_to_current=True) == [("8.14", "9.0")]

def test_consecutive_plus_direct_to_current_no_dupes():
    pairs = all_delta_pairs(["8.12", "8.13", "8.14", "9.0"], compute_direct_to_current=True)
    assert ("8.12", "8.13") in pairs and ("8.13", "8.14") in pairs and ("8.14", "9.0") in pairs
    assert ("8.12", "9.0") in pairs and ("8.13", "9.0") in pairs
    assert pairs.count(("8.14", "9.0")) == 1  # penultimate->current not duplicated
```
- [ ] **Step 2: Fail.**
- [ ] **Step 3: Implement** (mirrors spec §9.8)
```python
from typing import List, Tuple

def consecutive_pairs(ids: List[str]) -> List[Tuple[str, str]]:
    return list(zip(ids, ids[1:]))

def direct_to_current_pairs(ids: List[str]) -> List[Tuple[str, str]]:
    current = ids[-1]
    penultimate = ids[-2] if len(ids) >= 2 else None
    return [(old, current) for old in ids[:-1] if old != penultimate]

def all_delta_pairs(ids: List[str], compute_direct_to_current: bool = True) -> List[Tuple[str, str]]:
    pairs = consecutive_pairs(ids)
    if compute_direct_to_current and len(ids) > 2:
        pairs.extend(direct_to_current_pairs(ids))
    return pairs
```
- [ ] **Step 4: PASS.**
- [ ] **Step 5: Commit** — `git commit -m "feat(loading): delta-pair computation"`

---

### Task 4: GraphStorePort + query templates

**Files:**
- Create: `rdf_differ/adapters/loading/graph_store_port.py`, `rdf_differ/adapters/loading/queries.py`
- Test: `tests/unit/loading/test_queries.py`

- [ ] **Step 1: Failing test** (templates parametrise without free strings)
```python
from rdf_differ.adapters.loading.queries import delta_update, BLANK_NODE_FILTERS
from rdf_differ.domain.loading.config import BlankNodePolicy

def test_delta_update_targets_correct_graphs_and_filters():
    sparql = delta_update(target_graph="http://g/ins", minuend="http://g/new",
                          subtrahend="http://g/old", policy=BlankNodePolicy.EXCLUDE)
    assert "GRAPH <http://g/ins>" in sparql
    assert "GRAPH <http://g/new>" in sparql and "MINUS" in sparql and "GRAPH <http://g/old>" in sparql
    assert "isIRI(?s)" in sparql

def test_document_only_policy_has_no_filter():
    sparql = delta_update("http://g/ins", "http://g/new", "http://g/old", BlankNodePolicy.DOCUMENT_ONLY)
    assert "isIRI" not in sparql
```
- [ ] **Step 2: Fail.**
- [ ] **Step 3: Implement** `queries.py` (constants, mirrors spec §8.10 / script `:259-280`)
```python
from rdf_differ.domain.loading.config import BlankNodePolicy

PREFIXES = """prefix skos-history: <http://purl.org/skos-history/>
prefix dsv: <http://purl.org/iso25964/DataSet/Versioning#>
prefix sd: <http://www.w3.org/ns/sparql-service-description#>
prefix dcterms: <http://purl.org/dc/terms/>
prefix dc: <http://purl.org/dc/elements/1.1/>
prefix xhv: <http://www.w3.org/1999/xhtml/vocab#>
prefix void: <http://rdfs.org/ns/void#>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
"""

BLANK_NODE_FILTERS = {
    BlankNodePolicy.EXCLUDE: "  FILTER isIRI(?s)\n  FILTER (isIRI(?o) || isLiteral(?o) || isNumeric(?o))",
    BlankNodePolicy.SKOLEMISE: "",        # skolemisation handled at load time
    BlankNodePolicy.DOCUMENT_ONLY: "",
}

def delta_update(target_graph: str, minuend: str, subtrahend: str, policy: BlankNodePolicy) -> str:
    return f"""{PREFIXES}
INSERT {{ GRAPH <{target_graph}> {{ ?s ?p ?o }} }}
WHERE {{
  GRAPH <{minuend}> {{ ?s ?p ?o }}
  MINUS {{ GRAPH <{subtrahend}> {{ ?s ?p ?o }} }}
{BLANK_NODE_FILTERS[policy]}
}}"""

def clear_graph(graph: str) -> str: return f"CLEAR GRAPH <{graph}>"
```

- [ ] **Step 3b: metadata template constants** — the version-history/metadata writes the loader needs (F4, F5, F6, F8, F11, F15). Each is a parametrised constant builder; add a unit test per builder asserting the target graph and key triples. Signatures (bodies follow spec §8.5–8.12 / script `:122-308`):
```python
def service_description_update(service_iri, service_dataset_iri, query_endpoint, dataset_title) -> str: ...   # F4 (spec §8.5)
def history_set_update(history_graph, scheme_uri, current_record, query_endpoint, history_graph_desc) -> str: ...  # F5 (spec §8.6)
def version_record_update(history_graph, record, history_graph_iri, identifier, date, version_graph_desc, version_graph) -> str: ...  # F6 (spec §8.8); omit dc:date triple when date is None
def prev_link_update(history_graph, new_record, old_record) -> str: ...   # F8 (spec §8.9)
def delta_metadata_update(history_graph, delta, old_record, new_record, del_component, ins_component, del_desc, ins_desc, del_graph, ins_graph) -> str: ...  # F11 (spec §8.11)
def register_named_graph_update(service_dataset_iri, graph_desc, graph_iri) -> str: ...   # F15 (spec §8.12)
def ask_graph_nonempty(named_graph) -> str: ...                 # validation (spec §10.2)
def ask_invalid_insertion(insertions_graph, new_graph) -> str: ...  # validation (spec §10.5)
def ask_invalid_deletion(deletions_graph, old_graph) -> str: ...    # validation (spec §10.5)
```
All use `PREFIXES`; all bind IRIs via `<{...}>` interpolation of values the caller already controls (never raw user text). No free strings in callers.

- [ ] **Step 4: Implement** `graph_store_port.py`
```python
from typing import Protocol
from rdf_differ.domain.loading.config import BlankNodePolicy

class GraphStoreError(Exception): ...

class GraphStorePort(Protocol):
    def load_graph(self, named_graph: str, file_path: str, content_type: str) -> None: ...
    def run_update(self, sparql_update: str) -> None: ...
    def ask(self, sparql_ask: str) -> bool: ...
    def count_graph(self, named_graph: str) -> int: ...
    def serialize_graph(self, named_graph: str, content_type: str) -> bytes: ...
    def clear_graph(self, named_graph: str) -> None: ...
```
- [ ] **Step 5: Run → PASS; Commit** — `git commit -m "feat(loading): GraphStorePort and parametrised query templates"`

---
### Task 5: PyoxigraphInMemoryStore adapter

**Files:**
- Create: `rdf_differ/adapters/loading/in_memory_store.py`
- Modify: `requirements/common.txt` (add `pyoxigraph~=0.5`)
- Test: `tests/unit/loading/test_in_memory_store.py`

- [ ] **Step 1: Failing test** (real delta semantics + blank-node exclusion)
```python
from rdf_differ.adapters.loading.in_memory_store import PyoxigraphInMemoryStore
from rdf_differ.adapters.loading.queries import delta_update
from rdf_differ.domain.loading.config import BlankNodePolicy

def test_insertions_are_new_minus_old(tmp_path):
    old = tmp_path / "o.ttl"; old.write_text('<http://ex/a> <http://ex/p> <http://ex/x> .')
    new = tmp_path / "n.ttl"; new.write_text(
        '<http://ex/a> <http://ex/p> <http://ex/x> .\n<http://ex/b> <http://ex/p> <http://ex/y> .')
    store = PyoxigraphInMemoryStore()
    store.load_graph("http://g/old", str(old), "text/turtle")
    store.load_graph("http://g/new", str(new), "text/turtle")
    store.run_update(delta_update("http://g/ins", "http://g/new", "http://g/old", BlankNodePolicy.EXCLUDE))
    assert store.count_graph("http://g/ins") == 1  # only b p y

def test_blank_nodes_excluded(tmp_path):
    new = tmp_path / "n.ttl"; new.write_text('[] <http://ex/p> <http://ex/y> .')
    old = tmp_path / "o.ttl"; old.write_text('')
    store = PyoxigraphInMemoryStore()
    store.load_graph("http://g/old", str(old), "text/turtle")
    store.load_graph("http://g/new", str(new), "text/turtle")
    store.run_update(delta_update("http://g/ins", "http://g/new", "http://g/old", BlankNodePolicy.EXCLUDE))
    assert store.count_graph("http://g/ins") == 0
```
- [ ] **Step 2: Fail** (`pip install pyoxigraph` first; add to requirements).
- [ ] **Step 3: Implement**
```python
import io
from pyoxigraph import Store, RdfFormat, NamedNode
from rdf_differ.adapters.loading.graph_store_port import GraphStoreError

_FORMATS = {"text/turtle": RdfFormat.TURTLE, "application/rdf+xml": RdfFormat.RDF_XML,
            "application/n-triples": RdfFormat.N_TRIPLES}

class PyoxigraphInMemoryStore:
    def __init__(self): self._store = Store()
    def load_graph(self, named_graph, file_path, content_type):
        try:
            self._store.bulk_load(path=file_path, format=_FORMATS[content_type],
                                  to_graph=NamedNode(named_graph))
        except Exception as e:  # noqa: BLE001 - boundary translation
            raise GraphStoreError(f"load failed for {named_graph}: {e}") from e
    def run_update(self, sparql_update): self._store.update(sparql_update)
    def ask(self, sparql_ask): return bool(self._store.query(sparql_ask))
    def count_graph(self, named_graph):
        r = self._store.query(f"SELECT (COUNT(*) AS ?c) WHERE {{ GRAPH <{named_graph}> {{ ?s ?p ?o }} }}")
        return int(next(iter(r))["c"].value)
    def serialize_graph(self, named_graph, content_type):
        buf = io.BytesIO(); self._store.dump(buf, _FORMATS[content_type], from_graph=NamedNode(named_graph))
        return buf.getvalue()
    def clear_graph(self, named_graph): self._store.update(f"CLEAR GRAPH <{named_graph}>")
```
- [ ] **Step 4: PASS.**
- [ ] **Step 5: Commit** — `git commit -m "feat(loading): pyoxigraph in-memory GraphStore adapter"`

---

### Task 6: RemoteSparqlStore adapter

**Files:**
- Create: `rdf_differ/adapters/loading/remote_store.py`
- Test: `tests/unit/loading/test_remote_store.py`

- [ ] **Step 1: Failing test** (verbs/targets, mocked HTTP)
```python
from unittest.mock import MagicMock
from rdf_differ.adapters.loading.remote_store import RemoteSparqlStore
from rdf_differ.adapters.loading.graph_store_port import GraphStoreError
import pytest

def test_load_graph_uses_gsp_put(tmp_path):
    f = tmp_path / "v.ttl"; f.write_text("<http://ex/a> <http://ex/p> <http://ex/x> .")
    http = MagicMock(); http.put.return_value.status_code = 200
    store = RemoteSparqlStore(gsp_endpoint="http://fuseki/stw/data",
                              update_endpoint="http://fuseki/stw/update",
                              query_endpoint="http://fuseki/stw/sparql", http_client=http)
    store.load_graph("http://g/9.0", str(f), "text/turtle")
    args, kwargs = http.put.call_args
    assert kwargs["params"] == {"graph": "http://g/9.0"}

def test_http_error_raises(tmp_path):
    f = tmp_path / "v.ttl"; f.write_text("")
    http = MagicMock(); http.put.return_value.status_code = 500; http.put.return_value.text = "boom"
    store = RemoteSparqlStore("http://f/data", "http://f/update", "http://f/sparql", http_client=http)
    with pytest.raises(GraphStoreError):
        store.load_graph("http://g/9.0", str(f), "text/turtle")
```
- [ ] **Step 2: Fail.**
- [ ] **Step 3: Implement** (GSP `PUT` replaces `sparql_put` in script `:63-77`)
```python
from rdf_differ.adapters.loading.graph_store_port import GraphStoreError

class RemoteSparqlStore:
    def __init__(self, gsp_endpoint, update_endpoint, query_endpoint, http_client, auth=None):
        self._gsp, self._update_ep, self._query_ep = gsp_endpoint, update_endpoint, query_endpoint
        self._http, self._auth = http_client, auth
    def load_graph(self, named_graph, file_path, content_type):
        with open(file_path, "rb") as fh:
            resp = self._http.put(self._gsp, params={"graph": named_graph}, data=fh,
                                  headers={"Content-Type": content_type}, auth=self._auth, timeout=300)
        if resp.status_code >= 400:
            raise GraphStoreError(f"GSP PUT {named_graph} -> {resp.status_code}: {resp.text}")
    def run_update(self, sparql_update):
        resp = self._http.post(self._update_ep, data={"update": sparql_update}, auth=self._auth, timeout=120)
        if resp.status_code >= 400:
            raise GraphStoreError(f"UPDATE -> {resp.status_code}: {resp.text}")
    def ask(self, sparql_ask):
        resp = self._http.get(self._query_ep, params={"query": sparql_ask},
                              headers={"Accept": "application/sparql-results+json"}, timeout=120)
        if resp.status_code >= 400: raise GraphStoreError(f"ASK -> {resp.status_code}")
        return bool(resp.json().get("boolean"))
    def count_graph(self, named_graph):
        q = f"SELECT (COUNT(*) AS ?c) WHERE {{ GRAPH <{named_graph}> {{ ?s ?p ?o }} }}"
        resp = self._http.get(self._query_ep, params={"query": q},
                              headers={"Accept": "application/sparql-results+json"}, timeout=120)
        return int(resp.json()["results"]["bindings"][0]["c"]["value"])
    def serialize_graph(self, named_graph, content_type):
        resp = self._http.get(self._gsp, params={"graph": named_graph},
                              headers={"Accept": content_type}, timeout=120)
        return resp.content
    def clear_graph(self, named_graph): self.run_update(f"CLEAR GRAPH <{named_graph}>")
```
- [ ] **Step 4: PASS.**
- [ ] **Step 5: Commit** — `git commit -m "feat(loading): remote Fuseki GraphStore adapter (GSP + Update)"`

---

### Task 7: VersionStoreLoader service

**Files:**
- Create: `rdf_differ/services/loading/loader.py`
- Test: `tests/unit/loading/test_loader.py`

- [ ] **Step 1: Failing test** — a `FakeStore(GraphStorePort)` records updates; assert ordering (versions before deltas — script `:394-431`), CLEAR-before-INSERT (idempotency, L5), and pair coverage.
```python
from rdf_differ.services.loading.loader import VersionStoreLoader
from rdf_differ.domain.loading.config import VersionStoreConfig, VersionSpec

class FakeStore:
    """Records an ordered event log so ordering invariants are assertable."""
    def __init__(self): self.events=[]; self.loaded=[]
    def load_graph(self, g, f, c): self.loaded.append(g); self.events.append(("load", g))
    def run_update(self, u): self.events.append(("update", u))
    def clear_graph(self, g): self.events.append(("clear", g))
    def ask(self, q): return False
    def count_graph(self, g): return 1
    def serialize_graph(self, g, c): return b""

def test_loader_loads_all_versions_before_any_delta(tmp_path):
    f = tmp_path / "v.ttl"; f.write_text("")
    cfg = VersionStoreConfig("stw","http://ex/stw","http://ex/stw/version",
        [VersionSpec("8.14", f), VersionSpec("9.0", f)]).validate()
    store = FakeStore(); result = VersionStoreLoader(cfg, store).run()
    assert store.loaded[:2] == ["http://ex/stw/version/8.14", "http://ex/stw/version/9.0"]
    assert result["delta_pairs"] == [("8.14", "9.0")]

def test_each_delta_graph_is_cleared_before_it_is_written(tmp_path):
    f = tmp_path / "v.ttl"; f.write_text("")
    cfg = VersionStoreConfig("stw","http://ex/stw","http://ex/stw/version",
        [VersionSpec("8.14", f), VersionSpec("9.0", f)]).validate()
    store = FakeStore(); VersionStoreLoader(cfg, store).run()
    ins = "http://ex/stw/version/8.14/delta/9.0/insertions"
    clear_idx = next(i for i, e in enumerate(store.events) if e == ("clear", ins))
    write_idx = next(i for i, e in enumerate(store.events) if e[0] == "update" and ins in e[1])
    assert clear_idx < write_idx, "delta graph must be CLEARed before it is INSERTed (idempotency, L5)"
```
- [ ] **Step 2: Fail.**
- [ ] **Step 3: Implement** orchestration, depending only on `GraphStorePort`, `UriBuilder`, `queries`, `delta_pairs`, and `resolve_version_meta` (no `pyoxigraph`/`requests` import — enforced in Task 10):
  1. `cfg.validate()`.
  2. `run_update(service_description_update(...))` (F4) and `run_update(history_set_update(...))` with current = last version (F5).
  3. For each version: `load_graph(version_graph)`; resolve identifier/date (`resolve_version_meta`); `run_update(version_record_update(...))` (F6); `run_update(register_named_graph_update(...))` (F15).
  4. For each consecutive pair: `run_update(prev_link_update(...))` (F8).
  5. For each pair in `all_delta_pairs(...)`: `clear_graph(insertions)`, `clear_graph(deletions)`; `run_update(delta_update(insertions, new, old, policy))`; `run_update(delta_update(deletions, old, new, policy))`; `run_update(delta_metadata_update(...))` (F11); register both delta graphs (F15).
  6. Return `{dataset_id, current_version, delta_pairs, counts}` (counts via `count_graph`).
- [ ] **Step 4: PASS.**
- [ ] **Step 5: Commit** — `git commit -m "feat(loading): VersionStoreLoader orchestration service"`

---

### Task 8: Validation service

**Files:**
- Create: `rdf_differ/services/loading/validation.py`
- Test: `tests/unit/loading/test_validation.py`

- [ ] **Step 1: Failing test** — with a `FakeStore` whose `ask` returns `True` for "invalid insertion triple", `validate_store` raises `ValidationError`; with empty version graph (`count_graph==0`) it raises.
- [ ] **Step 2: Fail.**
- [ ] **Step 3: Implement** spec §10 checks via `ask`/`count_graph`: each version graph non-empty; each insertion triple ∈ new and ∉ old; each deletion triple ∈ old and ∉ new (ASK templates from `queries.py`). Raise `ValidationError` listing the offending graph.
- [ ] **Step 4: PASS.**
- [ ] **Step 5: Commit** — `git commit -m "feat(loading): post-load structural and content validation"`

---

### Task 9: CLI entrypoint

**Files:**
- Create: `rdf_differ/entrypoints/cli/load.py`
- Test: `tests/unit/loading/test_cli.py` (use `click.testing.CliRunner`)

- [ ] **Step 1: Failing test** — `CliRunner` invokes `load --config x.yaml --mode in-memory --out dir`; asserts exit 0 and a `result.json` with `validation: passed` for two tiny fixtures.
- [ ] **Step 2: Fail.**
- [ ] **Step 3: Implement** a `click` command: parse YAML → `VersionStoreConfig.validate()` → build store by `--mode` (`PyoxigraphInMemoryStore` or `RemoteSparqlStore` from `rdf_differ.config` endpoints) → `VersionStoreLoader(...).run()` → `validate_store(...)` → write serialised graphs + `result.json` to `--out`. Entrypoint only parses/wires/formats (no business logic).
- [ ] **Step 4: PASS.**
- [ ] **Step 5: Commit** — `git commit -m "feat(loading): CLI for in-memory and remote diffs"`

---

### Task 10: Integrate dual-mode, add contracts, retire the script

**Files:**
- Modify: `rdf_differ/adapters/diff_adapter.py:146-168` (`create_diff`)
- Create: `.importlinter`
- Delete: `resources/load_versions.sh`; `rdf_differ/adapters/skos_history_wrapper.py` subprocess path
- Modify: `tests/features/prepare_config.feature`, `tests/features/execute_skos_history.feature`

- [ ] **Step 1: Parity test (T6)** — feed the same two fixtures through (a) `RemoteSparqlStore` against a stubbed/dev Fuseki and (b) `PyoxigraphInMemoryStore`; assert identical insertion/deletion counts and identical named-graph IRI set. Also assert `FusekiDiffAdapter.dataset_description` and `count_inserted_triples`/`count_deleted_triples` (`__init__.py:67-118`) still return correct values against the new output.
- [ ] **Step 2: Fail** (create_diff still calls `SKOSHistoryRunner`).
- [ ] **Step 3: Add the GSP endpoint helper** — `FusekiDiffAdapter` today has only `make_sparql_endpoint` and `make_sparql_update_endpoint` (`diff_adapter.py:289-305`); `RemoteSparqlStore` also needs the Graph Store Protocol `/data` URL. Add:
```python
def make_gsp_endpoint(self, dataset_name: str) -> str:
    return urljoin(self.triplestore_service_url, dataset_name + "/data")
```
Then **rewire** `create_diff` (`diff_adapter.py:146-168`) to build `RemoteSparqlStore(gsp_endpoint=self.make_gsp_endpoint(dataset), update_endpoint=self.make_sparql_update_endpoint(dataset), query_endpoint=self.make_sparql_endpoint(dataset), http_client=self.http_client, auth=...)`, then run `VersionStoreLoader(cfg, store).run()` + `validate_store(...)`; remove the `SKOSHistoryRunner().run()` call.
- [ ] **Step 4: Add `.importlinter`**
```ini
[importlinter]
root_package = rdf_differ

[importlinter:contract:layers]
name = Loading module layering
type = layers
layers =
    rdf_differ.entrypoints
    rdf_differ.services
    rdf_differ.adapters
    rdf_differ.domain

[importlinter:contract:store-seam]
name = Services must not import concrete stores
type = forbidden
source_modules = rdf_differ.services.loading
forbidden_modules =
    pyoxigraph
    requests
    SPARQLWrapper
```
- [ ] **Step 5: Run** `pytest -q` and `lint-imports`; expected PASS. Delete `load_versions.sh` + subprocess code; adapt the two old feature files to describe the Python flow (or fold into `rdf_loading_module.feature`).
- [ ] **Step 6: Commit** — `git commit -m "feat(loading): dual-mode cutover; retire load_versions.sh; enforce contracts"`

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

- **Limitation → remediation:** L1→all (Python+tests); L2→Tasks 5/9; L3→Task 10 (delete subprocess); L4→Task 4 (templated, bound); L5→Tasks 5/7 (CLEAR before INSERT, asserted); L6/L7→Task 1 (`BlankNodePolicy` guard, `resolve_version_meta`); L8→Task 8; L9→Task 3; L10→Task 4/7 (explicit metadata graph).
- **EPIC task (1–9) → plan task (1–10):** EPIC 1→1–3; 2→4; 3→5; 4→6; 5→7; 6→8; 7→9; 8→10; 9→10 (`.importlinter`). The plan splits EPIC Task 1 (domain models) across plan Tasks 1–3.
- **Type consistency:** `GraphStorePort` method names (`load_graph`, `run_update`, `ask`, `count_graph`, `serialize_graph`, `clear_graph`) are identical across Tasks 4–10; `delta_update`/`clear_graph` query helpers used consistently; `VersionStoreConfig.validate()` returns self everywhere.
- **Placeholder scan:** Tasks 7–9 describe Step 3 orchestration in prose, but every write now binds to a **named template builder defined in Task 4 Step 3b** (`service_description_update`, `history_set_update`, `version_record_update`, `prev_link_update`, `delta_metadata_update`, `register_named_graph_update`) with its own failing test, so F4–F8/F11/F15 each have an executable target. Tasks 1–6 carry complete code.

## Execution Handoff
Plan saved. Recommended execution: **subagent-driven-development** (fresh subagent per task, review between tasks). The branch switch + commits are deferred per the user's instruction.

