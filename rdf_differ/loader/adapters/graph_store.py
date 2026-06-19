"""The triple-store port (ADR-1, DEC-2).

Engine-agnostic: ``RemoteSparqlStore``, ``PyoxigraphStore`` and ``RdflibStore``
implement ``GraphStorePort`` identically, so the loading service runs the same delta
logic against any of them. Services depend only on this Protocol (DIP) — never on a
store lib. The engine-selecting composition helper lives in ``graph_store_provider``
(kept separate so the concrete stores stay independent of each other).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class GraphStorePort(Protocol):
    """Replace/clear/update/query/serialize named graphs in a triple store."""

    def put_graph(self, graph_iri: str, data: bytes, content_type: str) -> None:
        """Replace a named graph's contents (GSP ``PUT`` semantics). Idempotent."""
        ...

    def clear_graph(self, graph_iri: str) -> None:
        """Empty a named graph (``CLEAR GRAPH``) before a delta recompute."""
        ...

    def update(self, sparql_update: str) -> None:
        """Run a SPARQL 1.1 Update (delta writes + metadata writes)."""
        ...

    def query(self, sparql_query: str) -> dict:
        """Run a SPARQL 1.1 SELECT/ASK and return SPARQL-JSON results."""
        ...

    def serialize(self, graph_iri: str, content_type: str = "text/turtle") -> bytes:
        """Export a named graph as RDF (for the in-memory diff artifacts)."""
        ...
