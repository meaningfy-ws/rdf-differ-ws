"""BDD step definitions for the in-memory RDF Loading Module diff (shipped by this Epic)."""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from rdf_differ.loader.adapters.in_memory_stores import PyoxigraphStore, RdflibStore
from rdf_differ.loader.domain.model import build_version_store_config
from rdf_differ.loader.services.loader import VersionStoreLoader, validate_store

scenarios("rdf_loading_module.feature")

OLD = "@prefix ex: <http://ex/> . ex:a ex:p ex:b . ex:a ex:p ex:gone ."
NEW = "@prefix ex: <http://ex/> . ex:a ex:p ex:b . ex:a ex:p ex:added ."
_ENGINES = {"oxigraph": PyoxigraphStore, "rdflib": RdflibStore}


@pytest.fixture
def context():
    return {}


@given("two RDF vocabulary versions that differ by one added and one removed triple")
def two_versions(context, tmp_path):
    old = tmp_path / "v1.ttl"
    new = tmp_path / "v2.ttl"
    old.write_text(OLD)
    new.write_text(NEW)
    context["config"] = build_version_store_config(
        {
            "dataset_id": "stw",
            "scheme_uri": "http://zbw.eu/stw",
            "versions": [{"id": "v1", "file": str(old)}, {"id": "v2", "file": str(new)}],
        }
    )


@when(parsers.parse("I load and diff them with the {engine} engine"))
def load_and_diff(context, engine):
    store = _ENGINES[engine]()
    context["store"] = store
    context["result"] = VersionStoreLoader(store).run(context["config"])


@then(parsers.parse("the insertions count is {count:d}"))
def insertions_count(context, count):
    assert context["result"].counts["v1->v2"].insertions == count


@then(parsers.parse("the deletions count is {count:d}"))
def deletions_count(context, count):
    assert context["result"].counts["v1->v2"].deletions == count


@then("the store validates")
def store_validates(context):
    validate_store(context["config"], context["store"])
