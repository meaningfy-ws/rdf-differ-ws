import pytest

from rdf_differ.adapters.loading import queries as q
from rdf_differ.adapters.loading.graph_store_port import GraphStorePort
from rdf_differ.adapters.loading.in_memory_oxigraph_store import PyoxigraphStore
from rdf_differ.adapters.loading.in_memory_rdflib_store import RdflibStore
from rdf_differ.domain.loading.blank_nodes import BlankNodePolicy

OLD = b"@prefix ex: <http://ex/> . ex:a ex:p ex:b . ex:a ex:p ex:old . _:x ex:p ex:y ."
NEW = b"@prefix ex: <http://ex/> . ex:a ex:p ex:b . ex:a ex:p ex:new . _:z ex:p ex:w ."

VOLD = "http://ex/version/old"
VNEW = "http://ex/version/new"
INS = "http://ex/version/old/delta/new/insertions"
DEL = "http://ex/version/old/delta/new/deletions"


@pytest.fixture(params=[PyoxigraphStore, RdflibStore], ids=["oxigraph", "rdflib"])
def store(request) -> GraphStorePort:
    return request.param()


def _count(store: GraphStorePort, graph: str) -> int:
    res = store.query(q.count_graph_query(graph))
    return int(res["results"]["bindings"][0]["c"]["value"])


def test_store_is_a_graph_store_port(store):
    assert isinstance(store, GraphStorePort)


def test_put_load_and_count(store):
    store.put_graph(VOLD, OLD, "text/turtle")
    assert _count(store, VOLD) == 3


def test_put_graph_is_idempotent(store):
    store.put_graph(VOLD, OLD, "text/turtle")
    store.put_graph(VOLD, OLD, "text/turtle")
    assert _count(store, VOLD) == 3


def test_delta_excludes_blank_nodes(store):
    store.put_graph(VOLD, OLD, "text/turtle")
    store.put_graph(VNEW, NEW, "text/turtle")
    store.update(q.delta_update(INS, VNEW, VOLD, BlankNodePolicy.EXCLUDE))
    store.update(q.delta_update(DEL, VOLD, VNEW, BlankNodePolicy.EXCLUDE))
    # insertions = new - old, blank nodes dropped -> only ex:a ex:p ex:new
    assert _count(store, INS) == 1
    # deletions = old - new -> only ex:a ex:p ex:old
    assert _count(store, DEL) == 1


def test_document_only_keeps_blank_node_change(store):
    store.put_graph(VOLD, OLD, "text/turtle")
    store.put_graph(VNEW, NEW, "text/turtle")
    store.update(q.delta_update(INS, VNEW, VOLD, BlankNodePolicy.DOCUMENT_ONLY))
    # ex:a ex:p ex:new AND the bnode triple _:z ex:p ex:w
    assert _count(store, INS) == 2


def test_ask_nonempty_and_clear(store):
    store.put_graph(VOLD, OLD, "text/turtle")
    assert store.query(q.ask_graph_nonempty_query(VOLD))["boolean"] is True
    store.clear_graph(VOLD)
    assert store.query(q.ask_graph_nonempty_query(VOLD))["boolean"] is False


def test_serialize_returns_bytes(store):
    store.put_graph(VOLD, OLD, "text/turtle")
    out = store.serialize(VOLD, "application/n-triples")
    assert isinstance(out, bytes) and b"http://ex/old" in out
