"""Blank-node handling policy and the pluggable strategy seam (DEC-9).

Pure domain. The ``BlankNodePolicy`` enum and the ``BlankNodeStrategy`` interface
live here; the rdflib-backed ``SKOLEMISE`` transform lives in the adapters layer
(it imports ``rdflib``, forbidden in ``domain`` by DEC-8). ``EXCLUDE`` and
``DOCUMENT_ONLY`` need no graph rewrite — they are realised as SPARQL filters in
the delta templates — so their strategy is the identity transform defined here.
"""

from enum import StrEnum
from typing import Protocol, runtime_checkable


class BlankNodePolicy(StrEnum):
    """How blank nodes participate in deltas."""

    EXCLUDE = "exclude"
    DOCUMENT_ONLY = "document_only"
    SKOLEMISE = "skolemise"


@runtime_checkable
class BlankNodeStrategy(Protocol):
    """Transforms parsed RDF *before* it is loaded into a graph store.

    Engine-agnostic: it operates on serialised RDF bytes, so it applies equally
    to the in-memory and remote stores. The transform must be deterministic.
    """

    policy: BlankNodePolicy

    def transform(self, data: bytes, *, content_type: str, base_iri: str) -> bytes:
        """Return the (possibly rewritten) RDF for loading."""
        ...


class IdentityBlankNodeStrategy:
    """No-op strategy for ``EXCLUDE`` / ``DOCUMENT_ONLY`` (pure, no rdflib).

    Filtering for ``EXCLUDE`` happens in the delta SPARQL templates, not here, so
    the bytes are returned unchanged.
    """

    policy: BlankNodePolicy

    def __init__(self, policy: BlankNodePolicy = BlankNodePolicy.EXCLUDE) -> None:
        if policy is BlankNodePolicy.SKOLEMISE:
            raise ValueError(
                "IdentityBlankNodeStrategy does not handle SKOLEMISE; "
                "use the rdflib skolemiser in the adapters layer"
            )
        self.policy = policy

    def transform(self, data: bytes, *, content_type: str, base_iri: str) -> bytes:
        return data
