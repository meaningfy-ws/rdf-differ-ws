"""Engine-selecting composition helper for the triple-store port.

``build_graph_store`` picks the concrete ``GraphStorePort`` for an ``Engine`` and is
used identically by the CLI and the API/Celery path. It lives apart from the port
module so the concrete stores remain independent of each other (the port carries no
import of any store); it sits in the adapters layer because it wires concrete
infrastructure — never in ``services`` (which must stay store-library-free, DIP).
"""

from rdf_differ.loader.adapters.graph_store import GraphStorePort
from rdf_differ.loader.adapters.in_memory_stores import PyoxigraphStore, RdflibStore
from rdf_differ.loader.adapters.remote_sparql_store import RemoteSparqlStore
from rdf_differ.loader.adapters.settings import StoreSettings
from rdf_differ.loader.domain.model import Engine


def build_graph_store(engine: Engine, settings: StoreSettings | None = None) -> GraphStorePort:
    """Construct the concrete ``GraphStorePort`` for ``engine``.

    In-memory engines ignore the settings; remote falls back to the
    environment-bound default ``StoreSettings``.
    """
    if engine is Engine.OXIGRAPH:
        return PyoxigraphStore()
    if engine is Engine.RDFLIB:
        return RdflibStore()
    return RemoteSparqlStore(settings or StoreSettings())
