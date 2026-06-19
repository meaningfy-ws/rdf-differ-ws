"""Unit tests for ``StoreSettings`` (adapters layer, DEC-10)."""

from rdf_differ.loader.adapters.settings import StoreSettings


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


def test_accepts_explicit_values():
    # StoreSettings is an injected value object (DEC-10): the composition root
    # builds it from `config`; it never reads the environment itself.
    settings = StoreSettings(
        location="http://fuseki.example",
        port=8080,
        username="bob",
        password="s3cret",
        retry_attempts=5,
    )

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
