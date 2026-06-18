"""In-memory ``GraphStorePort`` backed by rdflib (DEC-2).

Dependency-light, pure-Python SPARQL 1.1 Query + Update over an ``rdflib.Dataset``
of named graphs. Independent of the other store adapters (DEC-8). rdflib already
serialises SPARQL results as SPARQL-JSON, so ``query`` maps straight through.
"""

import json
from typing import cast

from rdflib import Dataset, URIRef

from rdf_differ.adapters.loading.graph_store_port import GraphStoreError

_MEDIA_TO_FORMAT = {
    "text/turtle": "turtle",
    "application/x-turtle": "turtle",
    "application/rdf+xml": "xml",
    "application/n-triples": "nt",
    "application/n-quads": "nquads",
    "application/trig": "trig",
    "text/n3": "n3",
    "application/ld+json": "json-ld",
}


def _format(content_type: str) -> str:
    fmt = _MEDIA_TO_FORMAT.get(content_type.split(";")[0].strip())
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
            graph.parse(data=data, format=_format(content_type))
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
                format=_format(content_type), encoding="utf-8"
            )
        except Exception as exc:
            raise GraphStoreError(f"rdflib serialize failed for <{graph_iri}>: {exc}") from exc
