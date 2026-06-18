# rdf-loading-module

Normative requirements for the RDF Loading Module — the Python replacement for
`resources/load_versions.sh`. Derived from `inputs/rdf_loading_module.feature`, the EPIC "Code of
practice", the "Features present in load_versions.sh (inventory to preserve)" table, and the
four-named-graph contract (`proposal.md` / `inputs/delta_graphs_loading_and_computation_spec.md`).

## ADDED Requirements

### Requirement: GraphStorePort store abstraction

The loading service SHALL depend only on a single secondary-adapter interface, `GraphStorePort`, for
all triple-store interaction, and SHALL NOT import `pyoxigraph`, `rdflib`, `requests`, `SPARQLWrapper`,
or `eds4jinja2` directly. Concrete stores SHALL be selected by dependency injection at the entrypoint,
so the same delta-computation logic runs unchanged behind any conforming adapter.

#### Scenario: Service depends only on the port

- **WHEN** the loading service computes deltas
- **THEN** it issues all store operations through `GraphStorePort` (`put_graph`, `clear_graph`, `update`, `query`, `serialize`)
- **AND** it imports no concrete triple-store or report library

#### Scenario: Concrete store chosen by injection

- **WHEN** the entrypoint runs a load with a selected engine
- **THEN** it constructs the matching `GraphStorePort` implementation and injects it into the service
- **AND** the service code is identical regardless of which implementation is injected

### Requirement: Config-selected storage backend (remote, oxigraph, rdflib)

The module SHALL support three interchangeable `GraphStorePort` implementations, the backend chosen by
configuration: a **remote** backend (`RemoteSparqlStore`) targeting any SPARQL 1.1 endpoint via the
Graph Store Protocol `PUT` plus SPARQL 1.1 Update/Query over HTTP; and two **in-memory** backends
requiring no triple store — `PyoxigraphStore` (via `pyoxigraph`) and `RdflibStore` (via `rdflib`). All
three backends SHALL produce equivalent results for the same configuration. The remote backend SHALL
NOT be specific to any single triple-store product.

#### Scenario: Run a temporary diff in memory without any triple store

- **WHEN** the user runs a valid load with versions "8.14" and "9.0" using an in-memory engine ("oxigraph" or "rdflib") and no triple store is available
- **THEN** the load completes successfully
- **AND** the insertions and deletions graphs can be exported as RDF files

#### Scenario: Produce equivalent results across all three backends

- **WHEN** the user runs the same valid configuration with the "remote", "oxigraph", and "rdflib" engines
- **THEN** the insertion and deletion counts match across the engines
- **AND** the same set of named graphs is produced by each engine

#### Scenario: Select the backend from configuration

- **WHEN** the configuration (or CLI flag) selects an engine of "remote", "oxigraph", or "rdflib"
- **THEN** the entrypoint constructs the matching `GraphStorePort` implementation
- **AND** an unknown engine value is rejected before any load begins

### Requirement: Triple-level delta computation

For each `(old, new)` version pair the module SHALL compute the insertions graph as
`triples(new) − triples(old)` and the deletions graph as `triples(old) − triples(new)`, applying the
configured blank-node policy. Identical versions SHALL yield empty insertions and deletions graphs.

#### Scenario: Compute insertions and deletions between two versions

- **WHEN** the deltas are computed for the pair "8.14" to "9.0"
- **THEN** the insertions graph contains exactly the triples present in "9.0" but absent from "8.14"
- **AND** the deletions graph contains exactly the triples present in "8.14" but absent from "9.0"
- **AND** the delta is described as having one insertions part and one deletions part, and records that it goes from "8.14" to "9.0"

#### Scenario: Identical versions produce empty deltas

- **WHEN** the two versions have identical content and the deltas are computed
- **THEN** the insertions graph is empty
- **AND** the deletions graph is empty

### Requirement: Configurable blank-node policy

The module SHALL apply a configurable `BlankNodePolicy` through a pluggable `BlankNodeStrategy` seam
during delta computation. The default `EXCLUDE` policy SHALL drop statements with a blank-node subject
(matching the legacy script); `DOCUMENT_ONLY` SHALL apply no filter; `SKOLEMISE` SHALL replace blank
nodes with W3C RDF 1.1 Skolem IRIs (`.well-known/genid/`) deterministically, so that the same input
yields identical Skolem IRIs across runs. The strategy SHALL be replaceable behind a stable interface
so the skolemisation algorithm can be improved later without changing callers.

#### Scenario: Exclude policy drops a blank-node statement

- **WHEN** a new version adds one statement with a blank-node subject and the policy is "exclude"
- **THEN** the blank-node statement is absent from the insertions graph

#### Scenario: Document-only policy keeps a blank-node statement

- **WHEN** a new version adds one statement with a blank-node subject and the policy is "document-only"
- **THEN** the blank-node statement is present in the insertions graph

#### Scenario: Skolemise policy replaces blank nodes deterministically

- **WHEN** a version containing a blank-node subject is loaded with the policy "skolemise"
- **THEN** each blank node is replaced by a W3C `.well-known/genid/` Skolem IRI
- **AND** loading the same input again yields identical Skolem IRIs (the transform is deterministic)

### Requirement: Configuration validation before any write

The module SHALL validate the loading configuration before writing any graph, and SHALL reject
configurations that have fewer than two versions, duplicate version identifiers, a missing version
file, a relative (non-absolute) scheme or base IRI, or mixed RDF file formats. The configuration model
SHALL be a typed value object that validates its own invariants at construction time, so an invalid
configuration cannot be represented. The reason SHALL be reported to the user.

#### Scenario: Reject invalid configurations before any data is written

- **WHEN** the user requests a load with a configuration that is invalid (missing one of two versions, duplicate version ids, a missing file, a relative scheme URI, or mixed RDF formats)
- **THEN** the load is rejected before any graph is written
- **AND** the user is told the reason (e.g. "at least two versions are required", "version identifiers must be unique", "version file does not exist", "scheme URI must be an absolute IRI", "all version files must share one format")

### Requirement: Delta-pair set covers consecutive and direct-to-current pairs

The module SHALL compute deltas for all consecutive `(old, new)` version pairs, and, when
direct-to-current computation is enabled and there are more than two versions, SHALL additionally
compute deltas from each earlier version to the current version without duplicating the
penultimate-to-current pair.

#### Scenario: Two versions yield a single pair

- **WHEN** the configuration has versions "8.14, 9.0" with direct-to-current enabled
- **THEN** deltas are computed for the pair "8.14->9.0" only

#### Scenario: Consecutive plus direct-to-current with no duplicates

- **WHEN** the configuration has versions "8.12, 8.13, 8.14, 9.0" with direct-to-current enabled
- **THEN** deltas are computed for "8.12->8.13, 8.13->8.14, 8.14->9.0, 8.12->9.0, 8.13->9.0"
- **AND** the penultimate-to-current pair "8.14->9.0" is not duplicated

#### Scenario: Direct-to-current disabled yields only consecutive pairs

- **WHEN** the configuration has versions "8.12, 8.13, 8.14, 9.0" with direct-to-current disabled
- **THEN** deltas are computed for "8.12->8.13, 8.13->8.14, 8.14->9.0" only

### Requirement: Preserve the four-named-graph contract and version history

The module SHALL materialise the named-graph contract consumed by `diff-query-generator` queries and
the report builder: one version named graph per version, an insertions graph and a deletions graph per
delta pair, and the version-history graph, together with their `sd:NamedGraph`/`sd:name` descriptions,
a version-history record per version, the `xhv:prev` chain between consecutive versions, and the
current version. Version identifier and date SHALL be resolved from the data, falling back to
configuration, with no dataset-specific names in code.

#### Scenario: Load two versions and record the version history

- **WHEN** the user runs a valid load with versions "8.14" and "9.0"
- **THEN** a named graph holds the complete content of version "8.14" and a named graph holds the complete content of version "9.0"
- **AND** a version history record exists for each version, the newer record points to the older as its previous version, and the history identifies "9.0" as the current version

#### Scenario: Keep distinct version graphs for awkward version identifiers

- **WHEN** the user runs a valid load with versions whose identifiers contain spaces or slashes (e.g. "v 1" and "v/2")
- **THEN** a distinct named graph holds the content of each version (identifiers safely encoded into the IRIs)

#### Scenario: Resolve version identifier and date from data or configuration

- **WHEN** a version file carries an embedded date, or omits it while the configuration supplies one, or both are absent
- **THEN** the version history record records the embedded date, the configured date, or no date respectively — without any dataset-specific branch in code

### Requirement: Idempotent re-runs

The module SHALL clear each delta graph before recomputing it, so that re-running the same load yields
equivalent graph state with no stale triples and unchanged insertion and deletion counts.

#### Scenario: Re-running the load produces equivalent graph state

- **WHEN** the user runs a configuration that has already been loaded once, again
- **THEN** each delta graph is cleared before it is recomputed
- **AND** the resulting insertion and deletion counts are unchanged and no stale triples remain from the previous run

### Requirement: Post-load validation

The module SHALL run structural and content validation after loading: each version graph SHALL be
non-empty, each insertion triple SHALL be present in the new version and absent from the old, and each
deletion triple SHALL be present in the old version and absent from the new. A parse failure SHALL
stop the load with a graph-load error naming the version; a validation failure SHALL name the
offending graph.

#### Scenario: Fail when a version file cannot be parsed as RDF

- **WHEN** the user runs a load whose version "9.0" file is not valid RDF
- **THEN** the load stops and reports a graph-load error naming version "9.0"

#### Scenario: Fail when a loaded version graph is unexpectedly empty

- **WHEN** the user runs a load whose version "9.0" file contains no statements
- **THEN** the load reports a validation failure naming the empty version

#### Scenario: Fail when an insertions graph contains a triple already present in the old version

- **WHEN** a completed load's insertions graph contains a triple that is also in the old version and the store is validated
- **THEN** the validation fails and identifies the offending insertions graph

### Requirement: Clear remote transport error handling with bounded retry

In remote mode the module SHALL surface triple-store transport failures (during upload, delta
computation, or validation) as a graph-store error whose message includes the reported failure, and
SHALL retry transient failures according to the configured retry policy before aborting.

#### Scenario: Surface a triple-store transport failure clearly

- **WHEN** the loading mode is remote and the triple store responds with a server error during upload, an update rejection during delta computation, or a query timeout during validation
- **THEN** the load stops and reports a graph-store error whose message includes the reported failure

#### Scenario: Retry a transient remote failure before aborting

- **WHEN** the loading mode is remote and the triple store fails transiently while uploading data
- **THEN** the failing remote step is retried according to the configured retry policy
- **AND** the load aborts with a graph-store error only after the retries are exhausted

### Requirement: No free strings; bound SPARQL templates

The module SHALL express SPARQL templates, prefixes, graph roles, blank-node policies, and MIME types
as constants or enumerations, SHALL build IRIs through a dedicated `UriBuilder`, and SHALL NOT
construct SPARQL by concatenating caller-supplied values as free strings. It SHALL NOT invoke
`subprocess`/`Popen` or shell out to `curl`.

#### Scenario: Delta queries are built from parametrised templates

- **WHEN** a delta update is constructed for given target, minuend, and subtrahend graphs and a blank-node policy
- **THEN** the query is produced from a named template constant binding those graph IRIs (not free-string concatenation of user text)
- **AND** the blank-node filter is present for the exclude policy and absent for the document-only policy

#### Scenario: No subprocess invocation

- **WHEN** the module loads versions and computes deltas
- **THEN** all store interaction happens through in-process Python calls via `GraphStorePort`, with no `subprocess`/`Popen` or `curl`

### Requirement: In-memory diff artifacts with no external dependency

When run with an in-memory engine the module SHALL produce diff artifacts — the version, insertions,
and deletions named graphs serialisable to RDF files, plus the insertion and deletion counts and a
validation outcome — without requiring a triple store and without requiring any reporting library. This
deliverable SHALL NOT depend on the eds4jinja2 report capability.

#### Scenario: Export diff artifacts from an in-memory run

- **WHEN** the user runs a valid load with an in-memory engine and requests diff artifacts only
- **THEN** the four named graphs are serialised to RDF files
- **AND** a machine-readable result reports the insertion and deletion counts and a validation outcome
- **AND** no triple store and no reporting library are required

### Requirement: Exposure through CLI and the async API

The module SHALL expose loading through a Click CLI accepting a configuration file, an engine
selection of "remote", "oxigraph", or "rdflib", and an optional report flag; and through the existing
create-diff API endpoint, which SHALL accept an engine/mode parameter and run asynchronously over the
existing task channel, reporting status and honouring the existing cancel/revoke path. For in-memory
engines the asynchronous worker SHALL build the store within the task lifetime.

#### Scenario: Run a load from the CLI selecting an engine

- **WHEN** the user runs the CLI with a valid configuration and an engine of "oxigraph", "rdflib", or "remote"
- **THEN** the matching backend is used and the load runs to completion
- **AND** the CLI writes the serialised graphs and a result document

#### Scenario: Run an asynchronous load through the API

- **WHEN** a client calls the create-diff endpoint with a valid configuration and an engine parameter
- **THEN** the load runs asynchronously on the existing task channel with observable status
- **AND** a cancellation request is honoured through the existing revoke path

### Requirement: In-memory full report depends on the eds4jinja2 capability with graceful fallback

The in-memory **full report** SHALL depend on an external eds4jinja2 capability that allows an
in-process SPARQL data source to be injected so report templates can query the in-process store. When
that capability is present, the module SHALL render the full report from the in-memory store with the
report templates unchanged. When that capability is absent, the module SHALL NOT fail the core load:
an in-memory run requesting a report SHALL degrade to remote-only and inform the user, and the
in-memory diff-artifacts deliverable SHALL remain unaffected.

#### Scenario: Render the in-memory full report when the capability is present

- **WHEN** the user requests a full report with an in-memory engine and the eds4jinja2 in-process data-source capability is available
- **THEN** the report is rendered by querying the in-process store
- **AND** the report templates are used unchanged

#### Scenario: Degrade gracefully when the capability is absent

- **WHEN** the user requests a full report with an in-memory engine and the eds4jinja2 in-process data-source capability is not available
- **THEN** the core load and the in-memory diff artifacts still succeed
- **AND** the report request degrades to remote-only and the user is informed
