"""Deterministic, W3C-compliant blank-node skolemisation (DEC-9).

Lives in the adapters layer because it imports ``rdflib`` (forbidden in ``domain``
by DEC-8). The initial KISS implementation is deterministic end-to-end:

1. ``rdflib.compare.to_canonical_graph`` assigns canonical blank-node labels that
   are stable across runs and parse order;
2. ``Graph.skolemize`` mints W3C RDF 1.1 Skolem IRIs of the form
   ``{base}/.well-known/genid/{label}``.

A richer canonicalisation can replace step 1 later behind the same
``BlankNodeStrategy`` interface, with no change for callers.
"""

from typing import cast

from rdflib import Graph
from rdflib.compare import to_canonical_graph

from rdf_differ.loader.domain.model import (
    BlankNodePolicy,
    BlankNodeStrategy,
    IdentityBlankNodeStrategy,
)

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

# rdflib's skolemize uses urljoin(authority, basepath + id); a leading slash on
# basepath would drop the authority's path, so use a trailing-slash authority and
# a *relative* basepath to land on {base}/.well-known/genid/{id}.
_GENID_BASEPATH = ".well-known/genid/"


class SkolemiseStrategy:
    """Rewrite blank nodes to deterministic W3C Skolem IRIs before load."""

    policy: BlankNodePolicy = BlankNodePolicy.SKOLEMISE

    def transform(self, data: bytes, *, content_type: str, base_iri: str) -> bytes:
        fmt = _MEDIA_TO_FORMAT.get(content_type.split(";")[0].strip(), "turtle")
        graph = Graph()
        graph.parse(data=data, format=fmt)
        canonical = to_canonical_graph(graph)
        authority = base_iri if base_iri.endswith("/") else base_iri + "/"
        skolemised = canonical.skolemize(authority=authority, basepath=_GENID_BASEPATH)
        return cast(bytes, skolemised.serialize(format=fmt, encoding="utf-8"))


def strategy_for(policy: BlankNodePolicy, *, base_iri: str = "") -> BlankNodeStrategy:
    """Return the strategy for a policy (composition-root helper).

    The ``base_iri`` is informational here; the loader passes the per-version base
    to ``transform`` at call time. In-memory engines and remote both use the same
    strategy because it operates on RDF before it reaches any store.
    """
    if policy is BlankNodePolicy.SKOLEMISE:
        return SkolemiseStrategy()
    return IdentityBlankNodeStrategy(policy)
