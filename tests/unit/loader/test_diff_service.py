from rdf_differ.loader.adapters.in_memory_stores import PyoxigraphStore
from rdf_differ.loader.domain.model import Engine
from rdf_differ.loader.services.diff_service import build_diff_config, create_version_diff

OLD = "@prefix ex: <http://ex/> . ex:a ex:p ex:b . ex:a ex:p ex:gone ."
NEW = "@prefix ex: <http://ex/> . ex:a ex:p ex:b . ex:a ex:p ex:added ."


def test_build_diff_config(tmp_path):
    old = tmp_path / "old.ttl"
    new = tmp_path / "new.ttl"
    old.write_text(OLD)
    new.write_text(NEW)
    cfg = build_diff_config(
        dataset="stw",
        scheme_uri="http://zbw.eu/stw",
        old_version_id="v1",
        new_version_id="v2",
        old_version_file=old,
        new_version_file=new,
        engine=Engine.OXIGRAPH,
    )
    assert cfg.version_ids == ["v1", "v2"]
    assert cfg.engine is Engine.OXIGRAPH


def test_create_version_diff_parity(tmp_path):
    old = tmp_path / "old.ttl"
    new = tmp_path / "new.ttl"
    old.write_text(OLD)
    new.write_text(NEW)
    cfg = build_diff_config(
        dataset="stw",
        scheme_uri="http://zbw.eu/stw",
        old_version_id="v1",
        new_version_id="v2",
        old_version_file=old,
        new_version_file=new,
        engine=Engine.OXIGRAPH,
    )
    store = PyoxigraphStore()
    result = create_version_diff(store, cfg)  # validate=True must not raise
    assert result.counts["v1->v2"].insertions == 1
    assert result.counts["v1->v2"].deletions == 1
