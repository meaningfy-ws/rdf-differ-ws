"""Shared domain-level constants (core component — importable by any component).

Pure data only — no I/O, no framework imports.
"""

from enum import StrEnum

# File-extension → RDF serialisation MIME type (used by the loader/CLI to declare
# the ``Content-Type`` when uploading a version file via the Graph Store Protocol).
INPUT_MIME_TYPES: dict[str, str] = {
    "rdf": "application/rdf+xml",
    "owl": "application/rdf+xml",
    "trix": "application/trix",
    "trig": "application/trig",
    "nq": "application/n-quads",
    "nt": "application/n-triples",
    "jsonld": "application/ld+json",
    "n3": "text/n3",
    "ttl": "text/turtle",
}

DEFAULT_INPUT_MIME_TYPE = "text/turtle"


class DeltaOp(StrEnum):
    """The two delta components computed for each ``(old, new)`` version pair."""

    INSERTIONS = "insertions"
    DELETIONS = "deletions"


def mime_type_for(file_name: str) -> str:
    """Return the RDF MIME type for a file name by its extension.

    Falls back to Turtle (the script's historical default) when the extension is
    unknown — callers that need strictness should validate the extension first.
    """
    suffix = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    return INPUT_MIME_TYPES.get(suffix, DEFAULT_INPUT_MIME_TYPE)
