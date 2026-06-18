"""Composition-root factory selecting a ``GraphStorePort`` per engine (DEC-10).

Used identically by the CLI and the API/Celery path: given an ``Engine`` (and, for
remote, a ``StoreSettings``), it builds the matching adapter. In-memory engines
ignore the settings; remote falls back to the environment-bound default.
"""

from rdf_differ.adapters.loading.graph_store_port import GraphStorePort
from rdf_differ.adapters.loading.in_memory_oxigraph_store import PyoxigraphStore
from rdf_differ.adapters.loading.in_memory_rdflib_store import RdflibStore
from rdf_differ.adapters.loading.remote_store import RemoteSparqlStore
from rdf_differ.adapters.loading.settings import StoreSettings
from rdf_differ.domain.loading.config import Engine


def build_graph_store(engine: Engine, settings: StoreSettings | None = None) -> GraphStorePort:
    """Construct the concrete ``GraphStorePort`` for ``engine``."""
    if engine is Engine.OXIGRAPH:
        return PyoxigraphStore()
    if engine is Engine.RDFLIB:
        return RdflibStore()
    return RemoteSparqlStore(settings or StoreSettings())
