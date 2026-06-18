"""Unit tests for ``StoreSettings`` (adapters layer, DEC-10)."""

from rdf_differ.adapters.loading.settings import StoreSettings


def test_defaults_mirror_config():
    settings = StoreSettings()
    assert settings.location == "http://localhost"
    assert settings.port == 3030
    assert settings.username == "admin"
    assert settings.password == ""
    assert settings.timeout == 30.0
    assert settings.retry_attempts == 3
    assert settings.retry_base_seconds == 1.0


def test_derived_endpoints_from_base():
    settings = StoreSettings()
    assert settings.base_endpoint == "http://localhost:3030"
    assert settings.data_endpoint == "http://localhost:3030/data"
    assert settings.update_endpoint == "http://localhost:3030/update"
    assert settings.query_endpoint == "http://localhost:3030/query"


def test_reads_env_with_prefix(monkeypatch):
    monkeypatch.setenv("RDF_DIFFER_FUSEKI_LOCATION", "http://fuseki.example")
    monkeypatch.setenv("RDF_DIFFER_FUSEKI_PORT", "8080")
    monkeypatch.setenv("RDF_DIFFER_FUSEKI_USERNAME", "bob")
    monkeypatch.setenv("RDF_DIFFER_FUSEKI_PASSWORD", "s3cret")
    monkeypatch.setenv("RDF_DIFFER_FUSEKI_RETRY_ATTEMPTS", "5")

    settings = StoreSettings()

    assert settings.base_endpoint == "http://fuseki.example:8080"
    assert settings.username == "bob"
    assert settings.password == "s3cret"
    assert settings.retry_attempts == 5
    assert settings.data_endpoint == "http://fuseki.example:8080/data"


def test_explicit_endpoint_overrides_win():
    settings = StoreSettings(
        data_endpoint_override="http://elsewhere/ds/data",
        update_endpoint_override="http://elsewhere/ds/update",
        query_endpoint_override="http://elsewhere/ds/query",
    )
    assert settings.data_endpoint == "http://elsewhere/ds/data"
    assert settings.update_endpoint == "http://elsewhere/ds/update"
    assert settings.query_endpoint == "http://elsewhere/ds/query"
