"""Version-diff use case — the Python replacement for ``load_versions.sh``.

Pure service (DIP): it receives an already-built ``GraphStorePort`` (the
composition root — the Celery task / CLI — constructs the concrete store and the
blank-node strategy), so it never imports a store library. It builds the
version-store config from two version files and runs the loader + validation.
"""

from pathlib import Path

from rdf_differ.adapters.loading.graph_store_port import GraphStorePort
from rdf_differ.domain.loading.blank_nodes import BlankNodeStrategy
from rdf_differ.domain.loading.config import Engine, VersionSpec, VersionStoreConfig
from rdf_differ.domain.loading.results import LoadResult
from rdf_differ.services.loading.loader import VersionStoreLoader
from rdf_differ.services.loading.validation import validate_store


def build_diff_config(
    *,
    dataset: str,
    scheme_uri: str,
    old_version_id: str,
    new_version_id: str,
    old_version_file: str | Path,
    new_version_file: str | Path,
    engine: Engine = Engine.REMOTE,
) -> VersionStoreConfig:
    """Build a two-version ``VersionStoreConfig`` from create-diff inputs."""
    return VersionStoreConfig(
        dataset_id=dataset,
        scheme_uri=scheme_uri,
        engine=engine,
        versions=[
            VersionSpec(id=old_version_id, file=Path(old_version_file)),
            VersionSpec(id=new_version_id, file=Path(new_version_file)),
        ],
    )


def create_version_diff(
    store: GraphStorePort,
    config: VersionStoreConfig,
    *,
    blank_node_strategy: BlankNodeStrategy | None = None,
    query_endpoint: str = "",
    validate: bool = True,
) -> LoadResult:
    """Load the versions and compute the deltas through the injected store."""
    result = VersionStoreLoader(
        store, blank_node_strategy=blank_node_strategy, query_endpoint=query_endpoint
    ).run(config)
    if validate:
        validate_store(config, store)
    return result
