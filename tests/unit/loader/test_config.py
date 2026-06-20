import pytest

from rdf_differ.loader.domain.exceptions import ConfigError
from rdf_differ.loader.domain.model import (
    BlankNodePolicy,
    Engine,
    ResolvedVersionMeta,
    VersionSpec,
    build_version_store_config,
    resolve_version_meta,
)


@pytest.fixture
def two_files(tmp_path):
    a = tmp_path / "v1.ttl"
    b = tmp_path / "v2.ttl"
    a.write_text("# a")
    b.write_text("# b")
    return a, b


def _cfg(files, **overrides):
    data = {
        "dataset_id": "stw",
        "scheme_uri": "http://zbw.eu/stw",
        "versions": [{"id": f"v{i}", "file": str(f)} for i, f in enumerate(files)],
    }
    data.update(overrides)
    return data


def test_valid_config(two_files):
    cfg = build_version_store_config(_cfg(two_files, engine="oxigraph"))
    assert cfg.engine is Engine.OXIGRAPH
    assert cfg.blank_node_policy is BlankNodePolicy.EXCLUDE
    assert cfg.version_ids == ["v0", "v1"]
    assert cfg.current_version == "v1"


def test_skolemise_policy_is_accepted(two_files):
    cfg = build_version_store_config(_cfg(two_files, blank_node_policy="skolemise"))
    assert cfg.blank_node_policy is BlankNodePolicy.SKOLEMISE


def test_rejects_single_version(two_files):
    a, _ = two_files
    with pytest.raises(ConfigError, match="at least two versions are required"):
        build_version_store_config(_cfg([a]))


def test_rejects_duplicate_ids(two_files):
    a, b = two_files
    data = _cfg(two_files)
    data["versions"][1]["id"] = data["versions"][0]["id"]
    with pytest.raises(ConfigError, match="version identifiers must be unique"):
        build_version_store_config(data)


def test_rejects_missing_file(tmp_path):
    real = tmp_path / "v1.ttl"
    real.write_text("# a")
    data = _cfg([real])
    data["versions"].append({"id": "v1", "file": str(tmp_path / "does-not-exist.ttl")})
    with pytest.raises(ConfigError):
        build_version_store_config(data)


def test_rejects_relative_scheme_uri(two_files):
    with pytest.raises(ConfigError, match="scheme URI must be an absolute IRI"):
        build_version_store_config(_cfg(two_files, scheme_uri="not-absolute"))


def test_rejects_mixed_formats(tmp_path):
    a = tmp_path / "v1.ttl"
    b = tmp_path / "v2.rdf"
    a.write_text("# a")
    b.write_text("# b")
    with pytest.raises(ConfigError, match="all version files must share one format"):
        build_version_store_config(_cfg([a, b]))


def test_resolve_meta_data_wins():
    spec = VersionSpec(id="9.0", file=__file__, identifier="cfg-id", date="2020-01-01")
    meta = resolve_version_meta(spec, data_identifier="data-id", data_date="2024-12-31")
    assert meta == ResolvedVersionMeta(identifier="data-id", date="2024-12-31")


def test_resolve_meta_config_fallback():
    spec = VersionSpec(id="9.0", file=__file__, identifier="cfg-id", date="2020-01-01")
    assert resolve_version_meta(spec) == ResolvedVersionMeta(identifier="cfg-id", date="2020-01-01")


def test_resolve_meta_both_absent_falls_back_to_id():
    spec = VersionSpec(id="9.0", file=__file__)
    assert resolve_version_meta(spec) == ResolvedVersionMeta(identifier="9.0", date=None)
