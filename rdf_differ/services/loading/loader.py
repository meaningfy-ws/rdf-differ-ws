"""Version-store loading + delta computation orchestration (service layer).

Depends only on the ``GraphStorePort``, the query templates, and pure domain
helpers — never on a store library (DEC-2/DEC-8). The same orchestration runs
against any engine. Mirrors ``load_versions.sh``: a first pass loads every version
+ its record, a second pass computes deltas (consecutive + direct-to-current),
each delta graph CLEARed before INSERT for idempotency (L5).
"""

import logging
from pathlib import Path

from rdf_differ.adapters.loading import queries as q
from rdf_differ.adapters.loading.graph_store_port import GraphStorePort
from rdf_differ.config import RDF_DIFFER_LOGGER
from rdf_differ.domain.constants import DeltaOp, mime_type_for
from rdf_differ.domain.loading.blank_nodes import BlankNodeStrategy, IdentityBlankNodeStrategy
from rdf_differ.domain.loading.config import VersionStoreConfig, resolve_version_meta
from rdf_differ.domain.loading.delta_pairs import consecutive_pairs, direct_to_current_pairs
from rdf_differ.domain.loading.results import DeltaCounts, LoadResult
from rdf_differ.domain.loading.uris import UriBuilder

logger = logging.getLogger(RDF_DIFFER_LOGGER)


class VersionStoreLoader:
    """Loads versions and builds the skos-history four-graph delta store."""

    def __init__(
        self,
        store: GraphStorePort,
        *,
        blank_node_strategy: BlankNodeStrategy | None = None,
        query_endpoint: str = "",
    ) -> None:
        self._store = store
        self._strategy = blank_node_strategy or IdentityBlankNodeStrategy()
        self._query_endpoint = query_endpoint

    def run(self, config: VersionStoreConfig) -> LoadResult:
        uri = UriBuilder(config.scheme_uri, config.base_version_iri)
        endpoint = self._query_endpoint or uri.base
        policy = config.blank_node_policy

        self._init_service_and_history(config, uri, endpoint)
        for spec in config.versions:
            self._load_version(config, uri, spec)

        version_ids = config.version_ids
        for old, new in consecutive_pairs(version_ids):
            self._load_delta(uri, old, new, policy)
            self._store.update(
                q.prev_link_update(uri.history_graph(), uri.record(new), uri.record(old))
            )
        if config.compute_direct_to_current:
            for old, new in direct_to_current_pairs(version_ids):
                self._load_delta(uri, old, new, policy)

        pairs = self._pairs(uri, version_ids, config.compute_direct_to_current)
        counts = self._collect_counts(uri, version_ids, config.compute_direct_to_current)
        return LoadResult(
            dataset_id=config.dataset_id,
            current_version=config.current_version,
            delta_pairs=pairs,
            counts=counts,
        )

    # --- steps --------------------------------------------------------------------
    def _init_service_and_history(
        self, config: VersionStoreConfig, uri: UriBuilder, endpoint: str
    ) -> None:
        self._store.update(
            q.service_description_update(
                uri.service(), uri.service_description(), endpoint, config.dataset_id
            )
        )
        self._store.update(
            q.history_set_update(
                uri.history_graph(),
                uri.scheme_uri,
                uri.record(config.current_version),
                endpoint,
                uri.history_named_graph_node(),
            )
        )
        self._store.update(
            q.register_named_graph_update(
                uri.service_description(), uri.history_named_graph_node(), uri.history_graph()
            )
        )

    def _load_version(self, config: VersionStoreConfig, uri: UriBuilder, spec) -> None:
        path = Path(str(spec.file))
        content_type = mime_type_for(path.name)
        data = self._strategy.transform(
            path.read_bytes(), content_type=content_type, base_iri=uri.base
        )
        version_graph = uri.version_graph(spec.id)
        self._store.put_graph(version_graph, data, content_type)

        data_identifier, data_date = self._extract_meta(uri, version_graph)
        meta = resolve_version_meta(spec, data_identifier=data_identifier, data_date=data_date)
        self._store.update(
            q.version_record_update(
                uri.history_graph(),
                uri.record(spec.id),
                version_graph,
                uri.version_named_graph_node(spec.id),
                meta.identifier,
                meta.date,
            )
        )
        self._store.update(
            q.register_named_graph_update(
                uri.service_description(), uri.version_named_graph_node(spec.id), version_graph
            )
        )

    def _load_delta(self, uri: UriBuilder, old: str, new: str, policy) -> None:
        delta = uri.delta(old, new)
        self._store.update(
            q.delta_metadata_update(uri.history_graph(), uri.record(old), uri.record(new), delta)
        )
        for op in (DeltaOp.INSERTIONS, DeltaOp.DELETIONS):
            minuend, subtrahend = (new, old) if op is DeltaOp.INSERTIONS else (old, new)
            op_graph = uri.delta_op_graph(old, new, op)
            self._store.clear_graph(op_graph)
            self._store.update(
                q.delta_update(
                    op_graph, uri.version_graph(minuend), uri.version_graph(subtrahend), policy
                )
            )
            self._store.update(
                q.delta_part_update(
                    uri.history_graph(),
                    delta,
                    op_graph,
                    uri.delta_op_named_graph_node(old, new, op),
                    op,
                )
            )
            self._store.update(
                q.register_named_graph_update(
                    uri.service_description(), uri.delta_op_named_graph_node(old, new, op), op_graph
                )
            )

    def _extract_meta(self, uri: UriBuilder, version_graph: str) -> tuple[str | None, str | None]:
        try:
            result = self._store.query(q.extract_version_meta_query(version_graph, uri.scheme_uri))
        except Exception:
            return None, None
        bindings = result.get("results", {}).get("bindings", [])
        if not bindings:
            return None, None
        row = bindings[0]
        ident = row.get("identifier", {}).get("value") or None
        date = row.get("date", {}).get("value") or None
        return ident, date

    def _pairs(
        self, uri: UriBuilder, version_ids: list[str], direct: bool
    ) -> list[tuple[str, str]]:
        pairs = list(consecutive_pairs(version_ids))
        if direct:
            pairs += direct_to_current_pairs(version_ids)
        return pairs

    def _collect_counts(self, uri: UriBuilder, version_ids: list[str], direct: bool):
        counts: dict[str, DeltaCounts] = {}
        for old, new in self._pairs(uri, version_ids, direct):
            ins = self._count(uri.delta_op_graph(old, new, DeltaOp.INSERTIONS))
            dele = self._count(uri.delta_op_graph(old, new, DeltaOp.DELETIONS))
            counts[LoadResult.pair_key(old, new)] = DeltaCounts(insertions=ins, deletions=dele)
        return counts

    def _count(self, graph_iri: str) -> int:
        result = self._store.query(q.count_graph_query(graph_iri))
        bindings = result.get("results", {}).get("bindings", [])
        return int(bindings[0]["c"]["value"]) if bindings else 0
