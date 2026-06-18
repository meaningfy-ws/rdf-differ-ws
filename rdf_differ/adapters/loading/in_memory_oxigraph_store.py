"""In-memory ``GraphStorePort`` backed by pyoxigraph (DEC-2).

Fast, native SPARQL 1.1 Query + Update over an in-process ``Store``. Independent
of the other store adapters (DEC-8). Engine/transport failures are translated to
``GraphStoreError``.
"""

import io
from typing import cast

import pyoxigraph as ox

from rdf_differ.adapters.loading.graph_store_port import GraphStoreError

_MEDIA_TO_FORMAT = {
    "text/turtle": ox.RdfFormat.TURTLE,
    "application/x-turtle": ox.RdfFormat.TURTLE,
    "application/rdf+xml": ox.RdfFormat.RDF_XML,
    "application/n-triples": ox.RdfFormat.N_TRIPLES,
    "application/n-quads": ox.RdfFormat.N_QUADS,
    "application/trig": ox.RdfFormat.TRIG,
    "text/n3": ox.RdfFormat.N3,
}


def _format(content_type: str) -> "ox.RdfFormat":
    fmt = _MEDIA_TO_FORMAT.get(content_type.split(";")[0].strip())
    if fmt is None:
        raise GraphStoreError(f"unsupported RDF media type for oxigraph: {content_type}")
    return fmt


def _term_to_json(term: object) -> dict:
    if isinstance(term, ox.NamedNode):
        return {"type": "uri", "value": term.value}
    if isinstance(term, ox.BlankNode):
        return {"type": "bnode", "value": term.value}
    if isinstance(term, ox.Literal):
        out = {"type": "literal", "value": term.value}
        if term.language:
            out["xml:lang"] = term.language
        elif term.datatype and term.datatype.value != "http://www.w3.org/2001/XMLSchema#string":
            out["datatype"] = term.datatype.value
        return out
    return {"type": "literal", "value": str(term)}


class PyoxigraphStore:
    """A ``GraphStorePort`` over an in-process ``pyoxigraph.Store``."""

    def __init__(self) -> None:
        self._store = ox.Store()

    def put_graph(self, graph_iri: str, data: bytes, content_type: str) -> None:
        graph = ox.NamedNode(graph_iri)
        try:
            self._store.update(f"CLEAR SILENT GRAPH <{graph_iri}>")
            self._store.load(io.BytesIO(data), format=_format(content_type), to_graph=graph)
        except Exception as exc:
            raise GraphStoreError(f"oxigraph load failed for <{graph_iri}>: {exc}") from exc

    def clear_graph(self, graph_iri: str) -> None:
        self.update(f"CLEAR SILENT GRAPH <{graph_iri}>")

    def update(self, sparql_update: str) -> None:
        try:
            self._store.update(sparql_update)
        except Exception as exc:
            raise GraphStoreError(f"oxigraph update failed: {exc}") from exc

    def query(self, sparql_query: str) -> dict:
        try:
            result = self._store.query(sparql_query)
        except Exception as exc:
            raise GraphStoreError(f"oxigraph query failed: {exc}") from exc
        if isinstance(result, (bool, ox.QueryBoolean)):
            return {"head": {}, "boolean": bool(result)}
        if not isinstance(result, ox.QuerySolutions):
            raise GraphStoreError("unexpected query result type (expected SELECT or ASK)")
        variables = [v.value for v in result.variables]
        bindings = []
        for solution in result:
            row = {}
            for var in result.variables:
                term = solution[var]
                if term is not None:
                    row[var.value] = _term_to_json(term)
            bindings.append(row)
        return {"head": {"vars": variables}, "results": {"bindings": bindings}}

    def serialize(self, graph_iri: str, content_type: str = "text/turtle") -> bytes:
        try:
            return cast(
                bytes,
                self._store.dump(format=_format(content_type), from_graph=ox.NamedNode(graph_iri)),
            )
        except Exception as exc:
            raise GraphStoreError(f"oxigraph serialize failed for <{graph_iri}>: {exc}") from exc
