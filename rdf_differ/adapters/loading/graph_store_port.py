"""The single secondary-adapter port over a triple store (ADR-1, DEC-2).

Engine-agnostic: ``RemoteSparqlStore``, ``PyoxigraphStore`` and ``RdflibStore``
implement it identically, so the loading service runs the same delta logic against
any of them. Services depend only on this Protocol (DIP) — never on a store lib.
"""

from typing import Protocol, runtime_checkable

from rdf_differ.domain.loading.errors import LoadingError


class GraphStoreError(LoadingError):
    """A triple-store transport/engine failure (HTTP error, parse error, …).

    ``status`` carries the HTTP status when the failure came from a remote
    endpoint (used to decide whether a retry is worthwhile); ``None`` otherwise.
    """

    status: int | None = None


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
