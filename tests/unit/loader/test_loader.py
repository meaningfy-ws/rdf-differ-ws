import json

import pytest

from rdf_differ.loader.adapters.in_memory_stores import PyoxigraphStore, RdflibStore
from rdf_differ.loader.domain.model import build_version_store_config
from rdf_differ.loader.services.diff_service import write_artifacts
from rdf_differ.loader.services.loader import VersionStoreLoader, validate_store

OLD = "@prefix ex: <http://ex/> . ex:a ex:p ex:b . ex:a ex:p ex:gone ."
NEW = "@prefix ex: <http://ex/> . ex:a ex:p ex:b . ex:a ex:p ex:added ."


@pytest.fixture
def config(tmp_path):
    old = tmp_path / "v1.ttl"
    new = tmp_path / "v2.ttl"
    old.write_text(OLD)
    new.write_text(NEW)
    return build_version_store_config(
        {
            "dataset_id": "stw",
            "scheme_uri": "http://zbw.eu/stw",
            "versions": [{"id": "v1", "file": str(old)}, {"id": "v2", "file": str(new)}],
        }
    )


@pytest.fixture(params=[PyoxigraphStore, RdflibStore], ids=["oxigraph", "rdflib"])
def store(request):
    return request.param()


def test_loader_computes_correct_delta_counts(config, store):
    result = VersionStoreLoader(store).run(config)
    assert result.dataset_id == "stw"
    assert result.current_version == "v2"
    assert result.delta_pairs == [("v1", "v2")]
    counts = result.counts["v1->v2"]
    assert counts.insertions == 1  # ex:a ex:p ex:added
    assert counts.deletions == 1  # ex:a ex:p ex:gone


def test_validation_passes_for_loaded_store(config, store):
    VersionStoreLoader(store).run(config)
    validate_store(config, store)  # no raise


def test_idempotent_rerun(config, store):
    loader = VersionStoreLoader(store)
    first = loader.run(config)
    second = loader.run(config)
    assert first.counts == second.counts


def test_write_artifacts(config, store, tmp_path):
    result = VersionStoreLoader(store).run(config)
    out = write_artifacts(store, config, result, tmp_path / "out")
    assert (out / "result.json").exists()
    assert (out / "version_v1.nt").exists()
    assert (out / "delta_v1_v2_insertions.nt").exists()
    payload = json.loads((out / "result.json").read_text())
    assert payload["counts"]["v1->v2"]["insertions"] == 1


# --- ordering invariants via a recording fake -------------------------------------
class FakeStore:
    def __init__(self):
        self.log: list[tuple[str, str]] = []

    def put_graph(self, graph_iri, data, content_type):
        self.log.append(("put", graph_iri))

    def clear_graph(self, graph_iri):
        self.log.append(("clear", graph_iri))

    def update(self, sparql_update):
        kind = "delta" if "minus" in sparql_update else "update"
        self.log.append((kind, sparql_update))

    def query(self, sparql_query):
        if sparql_query.strip().startswith("ASK"):
            return {"head": {}, "boolean": True}
        if "COUNT" in sparql_query:
            return {"results": {"bindings": [{"c": {"value": "0"}}]}}
        return {"results": {"bindings": []}}

    def serialize(self, graph_iri, content_type="text/turtle"):
        return b""


def test_all_versions_loaded_before_any_delta(config):
    fake = FakeStore()
    VersionStoreLoader(fake).run(config)
    kinds = [k for k, _ in fake.log]
    first_delta = kinds.index("delta")
    last_put = max(i for i, k in enumerate(kinds) if k == "put")
    assert last_put < first_delta  # two-pass: all puts precede any delta computation


def test_each_delta_graph_cleared_before_insert(config):
    fake = FakeStore()
    VersionStoreLoader(fake).run(config)
    # the insertions delta graph must be CLEARed before the delta INSERT targets it
    ins_graph = "http://zbw.eu/stw/version/v1/delta/v2/insertions"
    clear_idx = next(i for i, (k, v) in enumerate(fake.log) if k == "clear" and v == ins_graph)
    delta_idx = next(i for i, (k, v) in enumerate(fake.log) if k == "delta" and ins_graph in v)
    assert clear_idx < delta_idx
