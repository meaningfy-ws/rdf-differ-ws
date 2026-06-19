"""IRI construction for the skos-history named-graph contract.

Mirrors the legacy ``load_versions.sh`` URI scheme (``:317-342`` and the
``load_version``/``load_delta`` functions), with one deliberate change recorded
in design ADR-3: version-history records use ``{base}/record/{id}`` (with a
slash) instead of the script's slash-less ``{base}record/{id}``. This is safe
because consumers discover records by type/property, never by record-IRI shape.

Pure domain — no I/O, no framework imports.
"""

from urllib.parse import quote

from rdf_differ.core.domain.constants import DeltaOp


def _strip_trailing_slash(iri: str) -> str:
    return iri[:-1] if iri.endswith("/") else iri


def _encode(version_id: str) -> str:
    """Percent-encode a version id so it is safe inside an IRI path segment."""
    return quote(version_id, safe="")


class UriBuilder:
    """Builds every IRI in the version store from the scheme URI.

    ``base`` is ``{scheme_uri}/version`` (the script's ``BASEURI``), with any
    trailing slash on the scheme handled exactly as the script does.
    """

    def __init__(self, scheme_uri: str, base_version_iri: str | None = None) -> None:
        self.scheme_uri = _strip_trailing_slash(scheme_uri)
        self.base = (
            _strip_trailing_slash(base_version_iri)
            if base_version_iri
            else f"{self.scheme_uri}/version"
        )

    # --- version graphs & records -------------------------------------------------
    def version_graph(self, version_id: str) -> str:
        return f"{self.base}/{_encode(version_id)}"

    def version_named_graph_node(self, version_id: str) -> str:
        return f"{self.base}/{_encode(version_id)}/ng"

    def record(self, version_id: str) -> str:
        return f"{self.base}/record/{_encode(version_id)}"

    # --- version history set ------------------------------------------------------
    def history_graph(self) -> str:
        """The version-history named graph IRI (== ``base``)."""
        return self.base

    def history_named_graph_node(self) -> str:
        return f"{self.base}/ng"

    # --- deltas -------------------------------------------------------------------
    def delta(self, old: str, new: str) -> str:
        return f"{self.base}/{_encode(old)}/delta/{_encode(new)}"

    def delta_op_graph(self, old: str, new: str, op: DeltaOp) -> str:
        return f"{self.delta(old, new)}/{op.value}"

    def delta_op_named_graph_node(self, old: str, new: str, op: DeltaOp) -> str:
        return f"{self.delta(old, new)}/{op.value}/ng"

    # --- service description ------------------------------------------------------
    def service(self) -> str:
        return f"{self.base}/sparql-service"

    def service_description(self) -> str:
        return f"{self.base}/sparql-service/dd"
