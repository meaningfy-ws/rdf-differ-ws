"""Version-diff use case + in-memory artifact output (services layer).

The Python replacement for ``load_versions.sh``. Pure service (DIP): it receives
an already-built ``GraphStorePort`` (the composition root — the Celery task / CLI —
constructs the concrete store and the blank-node strategy), so it never imports a
store library. ``create_version_diff`` runs the loader + validation;
``write_artifacts`` serialises the four named graphs + ``result.json`` — the
always-available in-memory deliverable, needing no triple store and no eds4jinja2.
"""

from pathlib import Path
from urllib.parse import quote

from rdf_differ.core.domain.constants import DeltaOp
from rdf_differ.loader.adapters.graph_store import GraphStorePort
from rdf_differ.loader.domain.model import (
    BlankNodeStrategy,
    Engine,
    LoadResult,
    VersionSpec,
    VersionStoreConfig,
)
from rdf_differ.loader.domain.uris import UriBuilder
from rdf_differ.loader.services.loader import VersionStoreLoader, validate_store

_SERIALISATION = "application/n-triples"
_EXT = "nt"


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


def _safe(name: str) -> str:
    return quote(name, safe="")


def write_artifacts(
    store: GraphStorePort, config: VersionStoreConfig, result: LoadResult, out_dir: str | Path
) -> Path:
    """Serialise the contract graphs + ``result.json`` into ``out_dir``; return it."""
    uri = UriBuilder(config.scheme_uri, config.base_version_iri)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    _dump(store, uri.history_graph(), out / f"version-history.{_EXT}")
    for spec in config.versions:
        _dump(store, uri.version_graph(spec.id), out / f"version_{_safe(spec.id)}.{_EXT}")
    for old, new in result.delta_pairs:
        for op in (DeltaOp.INSERTIONS, DeltaOp.DELETIONS):
            graph = uri.delta_op_graph(old, new, op)
            _dump(store, graph, out / f"delta_{_safe(old)}_{_safe(new)}_{op.value}.{_EXT}")

    (out / "result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return out


def _dump(store: GraphStorePort, graph_iri: str, target: Path) -> None:
    target.write_bytes(store.serialize(graph_iri, _SERIALISATION))
