"""Unit tests for ``build_graph_store`` (composition-root factory, DEC-10)."""

from rdf_differ.adapters.loading.graph_store_port import GraphStorePort
from rdf_differ.adapters.loading.in_memory_oxigraph_store import PyoxigraphStore
from rdf_differ.adapters.loading.in_memory_rdflib_store import RdflibStore
from rdf_differ.adapters.loading.remote_store import RemoteSparqlStore
from rdf_differ.adapters.loading.settings import StoreSettings
from rdf_differ.adapters.loading.store_factory import build_graph_store
from rdf_differ.domain.loading.config import Engine


def test_oxigraph_engine_builds_pyoxigraph_store():
    store = build_graph_store(Engine.OXIGRAPH)
    assert isinstance(store, PyoxigraphStore)
    assert isinstance(store, GraphStorePort)


def test_rdflib_engine_builds_rdflib_store():
    store = build_graph_store(Engine.RDFLIB)
    assert isinstance(store, RdflibStore)
    assert isinstance(store, GraphStorePort)


def test_remote_engine_builds_remote_store_with_given_settings():
    settings = StoreSettings(location="http://remote", port=9999)
    store = build_graph_store(Engine.REMOTE, settings)
    assert isinstance(store, RemoteSparqlStore)
    assert isinstance(store, GraphStorePort)


def test_remote_engine_defaults_settings_when_none():
    store = build_graph_store(Engine.REMOTE)
    assert isinstance(store, RemoteSparqlStore)
