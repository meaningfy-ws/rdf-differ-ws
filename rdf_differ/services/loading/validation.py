"""Post-load structural validation (service layer, spec §10).

Fails fast (``ValidationError``) when a version graph that must hold data is
empty — the silent-corruption gap (L8) the legacy script had. Delta graphs may
legitimately be empty (identical versions), so they are not asserted non-empty.
"""

from rdf_differ.adapters.loading import queries as q
from rdf_differ.adapters.loading.graph_store_port import GraphStorePort
from rdf_differ.domain.loading.config import VersionStoreConfig
from rdf_differ.domain.loading.errors import ValidationError
from rdf_differ.domain.loading.uris import UriBuilder


def validate_store(config: VersionStoreConfig, store: GraphStorePort) -> None:
    """Assert every version graph is non-empty; raise ``ValidationError`` otherwise."""
    uri = UriBuilder(config.scheme_uri, config.base_version_iri)
    for spec in config.versions:
        version_graph = uri.version_graph(spec.id)
        result = store.query(q.ask_graph_nonempty_query(version_graph))
        if not result.get("boolean", False):
            raise ValidationError(f"version graph <{version_graph}> is unexpectedly empty")
