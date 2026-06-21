"""Live-Fuseki verification of the diff-semantics filter relaxation (#142, #143).

EPIC: resolve-open-issues — Capability 3 (diff-semantics).

The sibling ``test_diff_semantics_queries.py`` executes the committed
``updated_property_*.rq`` templates against an in-memory ``rdflib.Dataset``. rdflib is a
fine SPARQL engine, but the templates run in production against *Fuseki* (Apache Jena).
This test closes that gap: it loads the SAME minimal skos-history fixture into a real
Fuseki dataset over SPARQL Update, runs the real lang-fallback ``updated_property``
query through ``FusekiDiffAdapter.execute_query``, and asserts the #142/#143 rows surface
on the real engine.

Marked ``@pytest.mark.integration`` (the repo auto-deselects integration tests by
default; ``make``/CI run them with services up). When no Fuseki is reachable the test
skips gracefully so a plain ``pytest`` run never errors.
"""

import contextlib
import uuid

import pytest
import rdflib
import requests

from rdf_differ import config
from rdf_differ.core.adapters.sparql import SPARQLRunner
from rdf_differ.diffing.adapters.diff_adapter import FusekiDiffAdapter

# Reuse the exact fixture vocabulary + builder helpers from the in-memory test so the
# two executions verify identical data. (We may only touch these two files, and
# importing the unit-test module is the clean way to share the fixture.)
from tests.unit.test_diff_semantics_queries import (
    CONCEPT,
    CONCEPT_CLASS,
    DEL_GRAPH,
    INS_GRAPH,
    LANG_FALLBACK_QUERY,
    NEW_GRAPH,
    OLD_GRAPH,
    PREF_LABEL,
    VHG,
    _metadata_turtle,
)

# A fixed, stable dataset name (no Math.random/Date) — cleaned up in a finally block.
# A run-unique suffix keeps parallel/concurrent runs from clobbering each other.
DATASET_NAME = f"diff_semantics_it_{uuid.uuid4().hex[:8]}"

PING_TIMEOUT_SECONDS = 2

L = rdflib.Literal
URI = rdflib.URIRef


def _fuseki_is_up() -> bool:
    """Probe Fuseki's ping endpoint; any connection problem means 'not up'."""
    ping_url = f"{config.RDF_DIFFER_FUSEKI_SERVICE}/$/ping"
    try:
        response = requests.get(ping_url, timeout=PING_TIMEOUT_SECONDS)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _insert_data_update(graph_iri: str, triples: str) -> str:
    """Wrap N-Triples-ish body in an INSERT DATA targeting a named graph."""
    return f"INSERT DATA {{ GRAPH <{graph_iri}> {{ {triples} }} }}"


def _term(node) -> str:
    """Serialise an rdflib term to SPARQL syntax (literal with tag / IRI)."""
    return node.n3()


def _load_fixture(adapter: FusekiDiffAdapter, old_value, new_value) -> None:
    """Emit the same skos-history layout as the in-memory test as SPARQL Updates.

    One INSERT DATA per named graph: version-history metadata, old version, new
    version, deletions, insertions.
    """
    concept = f"<{CONCEPT}>"
    pref = f"<{PREF_LABEL}>"
    cls = f"<{CONCEPT_CLASS}>"
    old_n3 = _term(old_value)
    new_n3 = _term(new_value)

    # version-history metadata graph (turtle -> n-triples for INSERT DATA body)
    metadata_graph = rdflib.Graph()
    metadata_graph.parse(data=_metadata_turtle(), format="turtle")
    metadata_triples = metadata_graph.serialize(format="nt")

    updates = [
        _insert_data_update(VHG, metadata_triples),
        _insert_data_update(OLD_GRAPH, f"{concept} a {cls} . {concept} {pref} {old_n3} ."),
        _insert_data_update(NEW_GRAPH, f"{concept} a {cls} . {concept} {pref} {new_n3} ."),
        _insert_data_update(DEL_GRAPH, f"{concept} {pref} {old_n3} ."),
        _insert_data_update(INS_GRAPH, f"{concept} {pref} {new_n3} ."),
    ]
    for update in updates:
        adapter.execute_update_query(dataset_name=DATASET_NAME, sparql_query=update)


def _run_query(adapter: FusekiDiffAdapter) -> list[dict]:
    """Run the real lang-fallback query and return SPARQL JSON bindings."""
    result = adapter.execute_query(
        dataset_name=DATASET_NAME, sparql_query=LANG_FALLBACK_QUERY.read_text()
    )
    return result["results"]["bindings"]


def _values(bindings: list[dict], var: str) -> set[str]:
    return {row[var]["value"] for row in bindings if var in row}


@pytest.mark.integration
def test_relaxed_filter_surfaces_updates_on_real_fuseki():
    """The #142/#143 cases surface as ``updated`` rows on a real Fuseki engine."""
    if not _fuseki_is_up():
        pytest.skip(
            f"Fuseki not reachable at {config.RDF_DIFFER_FUSEKI_SERVICE}; "
            "skipping live integration test."
        )

    adapter = FusekiDiffAdapter(config.RDF_DIFFER_FUSEKI_SERVICE, requests, SPARQLRunner())

    adapter.create_dataset(DATASET_NAME)
    try:
        # (a) #142 language-tag change: 'text'@en -> 'text'@fr
        _load_fixture(adapter, L("text", lang="en"), L("text", lang="fr"))
        bindings = _run_query(adapter)
        assert bindings, "language-tag change produced no update row on Fuseki"
        assert "text" in _values(bindings, "oldValue")
        assert "text" in _values(bindings, "newValue")

        # reset graphs between cases by recreating the dataset
        adapter.delete_dataset(DATASET_NAME)
        adapter.create_dataset(DATASET_NAME)

        # (b) #142 language-tag removal: 'text'@en -> 'text'
        _load_fixture(adapter, L("text", lang="en"), L("text"))
        bindings = _run_query(adapter)
        assert bindings, "language-tag removal produced no update row on Fuseki"

        adapter.delete_dataset(DATASET_NAME)
        adapter.create_dataset(DATASET_NAME)

        # (c) #143 literal -> IRI: 'label' -> <http://ex/iri>
        _load_fixture(adapter, L("label"), URI("http://ex/iri"))
        bindings = _run_query(adapter)
        assert bindings, "literal->IRI change produced no update row on Fuseki"
        assert "http://ex/iri" in _values(bindings, "newValue")

        adapter.delete_dataset(DATASET_NAME)
        adapter.create_dataset(DATASET_NAME)

        # (d) unchanged value must NOT be reported
        _load_fixture(adapter, L("text", lang="en"), L("text", lang="en"))
        bindings = _run_query(adapter)
        assert not bindings, f"unchanged value wrongly reported on Fuseki: {bindings}"
    finally:
        # The dataset may already be gone (a case branch deleted it before failing);
        # cleanup is best-effort and must never mask the real assertion failure.
        with contextlib.suppress(Exception):
            adapter.delete_dataset(DATASET_NAME)
