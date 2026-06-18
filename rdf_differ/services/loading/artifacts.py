"""In-memory diff-artifact output (service layer, DEC-5 — no external dependency).

Serialises the four named graphs (version graphs, per-pair insertions/deletions,
the version-history graph) to files and writes a machine-readable ``result.json``.
This is the always-ships in-memory deliverable; it needs no triple store and no
eds4jinja2.
"""

from pathlib import Path
from urllib.parse import quote

from rdf_differ.adapters.loading.graph_store_port import GraphStorePort
from rdf_differ.domain.constants import DeltaOp
from rdf_differ.domain.loading.config import VersionStoreConfig
from rdf_differ.domain.loading.results import LoadResult
from rdf_differ.domain.loading.uris import UriBuilder

_SERIALISATION = "application/n-triples"
_EXT = "nt"


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
