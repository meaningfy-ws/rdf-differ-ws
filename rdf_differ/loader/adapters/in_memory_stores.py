"""In-memory ``GraphStorePort`` backends (DEC-2): pyoxigraph and rdflib.

Two config-selected, dependency-light engines sharing one module. Neither imports
the other (DEC-8 independence holds within the module). ``PyoxigraphStore`` is
fast native SPARQL over an in-process ``Store``; ``RdflibStore`` is pure-Python
SPARQL over an ``rdflib.Dataset``. Both translate engine failures to
``GraphStoreError`` and return SPARQL-JSON from ``query``.
"""

import io
import json
from typing import cast

import pyoxigraph as ox
from rdflib import Dataset, URIRef

from rdf_differ.loader.adapters.exceptions import GraphStoreError

_OX_FORMATS = {
    "text/turtle": ox.RdfFormat.TURTLE,
    "application/x-turtle": ox.RdfFormat.TURTLE,
    "application/rdf+xml": ox.RdfFormat.RDF_XML,
    "application/n-triples": ox.RdfFormat.N_TRIPLES,
    "application/n-quads": ox.RdfFormat.N_QUADS,
    "application/trig": ox.RdfFormat.TRIG,
    "text/n3": ox.RdfFormat.N3,
}

_RDFLIB_FORMATS = {
    "text/turtle": "turtle",
    "application/x-turtle": "turtle",
    "application/rdf+xml": "xml",
    "application/n-triples": "nt",
    "application/n-quads": "nquads",
    "application/trig": "trig",
    "text/n3": "n3",
    "application/ld+json": "json-ld",
}


def _media(content_type: str) -> str:
    return content_type.split(";")[0].strip()


# --- pyoxigraph ---------------------------------------------------------------
def _ox_format(content_type: str) -> "ox.RdfFormat":
    fmt = _OX_FORMATS.get(_media(content_type))
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
            self._store.load(io.BytesIO(data), format=_ox_format(content_type), to_graph=graph)
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
                self._store.dump(
                    format=_ox_format(content_type), from_graph=ox.NamedNode(graph_iri)
                ),
            )
        except Exception as exc:
            raise GraphStoreError(f"oxigraph serialize failed for <{graph_iri}>: {exc}") from exc


# --- rdflib -------------------------------------------------------------------
def _rdflib_format(content_type: str) -> str:
    fmt = _RDFLIB_FORMATS.get(_media(content_type))
    if fmt is None:
        raise GraphStoreError(f"unsupported RDF media type for rdflib: {content_type}")
    return fmt


class RdflibStore:
    """A ``GraphStorePort`` over an in-memory ``rdflib.Dataset``."""

    def __init__(self) -> None:
        self._dataset = Dataset(default_union=False)

    def put_graph(self, graph_iri: str, data: bytes, content_type: str) -> None:
        try:
            self._dataset.remove_graph(self._dataset.graph(URIRef(graph_iri)))
            graph = self._dataset.graph(URIRef(graph_iri))
            graph.parse(data=data, format=_rdflib_format(content_type))
        except GraphStoreError:
            raise
        except Exception as exc:
            raise GraphStoreError(f"rdflib load failed for <{graph_iri}>: {exc}") from exc

    def clear_graph(self, graph_iri: str) -> None:
        self._dataset.remove_graph(self._dataset.graph(URIRef(graph_iri)))

    def update(self, sparql_update: str) -> None:
        try:
            self._dataset.update(sparql_update)
        except Exception as exc:
            raise GraphStoreError(f"rdflib update failed: {exc}") from exc

    def query(self, sparql_query: str) -> dict:
        try:
            result = self._dataset.query(sparql_query)
            return cast(dict, json.loads(cast(str, result.serialize(format="json"))))
        except Exception as exc:
            raise GraphStoreError(f"rdflib query failed: {exc}") from exc

    def serialize(self, graph_iri: str, content_type: str = "text/turtle") -> bytes:
        try:
            return self._dataset.graph(URIRef(graph_iri)).serialize(
                format=_rdflib_format(content_type), encoding="utf-8"
            )
        except Exception as exc:
            raise GraphStoreError(f"rdflib serialize failed for <{graph_iri}>: {exc}") from exc
