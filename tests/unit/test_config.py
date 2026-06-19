"""Unit tests for the Meaningfy config resolver (root ``rdf_differ.config``)."""

from rdf_differ import RdfDifferConfigResolver


def test_defaults_when_env_absent(monkeypatch):
    for var in (
        "RDF_DIFFER_FUSEKI_LOCATION",
        "RDF_DIFFER_FUSEKI_PORT",
        "RDF_DIFFER_USE_PYTHON_LOADER",
    ):
        monkeypatch.delenv(var, raising=False)
    config = RdfDifferConfigResolver()

    assert config.RDF_DIFFER_FUSEKI_SERVICE == "http://localhost:3030"
    assert config.RDF_DIFFER_LOGGER == "gunicorn.error"
    assert config.RDF_DIFFER_USE_PYTHON_LOADER is False
    assert isinstance(config.RDF_DIFFER_FUSEKI_PORT, int)


def test_reads_and_casts_env(monkeypatch):
    monkeypatch.setenv("RDF_DIFFER_FUSEKI_LOCATION", "http://fuseki.example")
    monkeypatch.setenv("RDF_DIFFER_FUSEKI_PORT", "8080")
    monkeypatch.setenv("RDF_DIFFER_USE_PYTHON_LOADER", "true")
    config = RdfDifferConfigResolver()

    assert config.RDF_DIFFER_FUSEKI_SERVICE == "http://fuseki.example:8080"
    assert config.RDF_DIFFER_FUSEKI_PORT == 8080
    assert config.RDF_DIFFER_USE_PYTHON_LOADER is True


def test_template_location_overrides_when_populated(tmp_path, monkeypatch):
    (tmp_path / "example").mkdir()
    monkeypatch.setenv("RDF_DIFFER_TEMPLATE_LOCATION", str(tmp_path))
    assert str(tmp_path) == RdfDifferConfigResolver().APPLICATION_PROFILES_ROOT_FOLDER
