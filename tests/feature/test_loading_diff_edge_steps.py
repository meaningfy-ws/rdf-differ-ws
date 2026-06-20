"""Steps for loading_diff_edge_cases.feature (EPIC behaviour-test-coverage).

Infra-free: in-memory engines (rdflib, pyoxigraph) via the loader service over small fixtures
and the existing sample OWL test data.
"""

from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from rdf_differ.loader.adapters.in_memory_stores import PyoxigraphStore, RdflibStore
from rdf_differ.loader.domain.model import build_version_store_config
from rdf_differ.loader.services.loader import VersionStoreLoader

scenarios("loading_diff_edge_cases.feature")

_ENGINES = {"oxigraph": PyoxigraphStore, "rdflib": RdflibStore}
_OWL = Path(__file__).resolve().parents[1] / "test_data" / "owl"
_SAME = "@prefix ex: <http://ex/> . ex:a ex:p ex:b ."


@pytest.fixture
def context():
    return {"error": None}


def _config(old, new):
    return build_version_store_config(
        {
            "dataset_id": "ds",
            "scheme_uri": "http://example.org/scheme",
            "versions": [{"id": "v1", "file": str(old)}, {"id": "v2", "file": str(new)}],
        }
    )


@given("two identical RDF vocabulary versions")
def _identical(context, tmp_path):
    old, new = tmp_path / "v1.ttl", tmp_path / "v2.ttl"
    old.write_text(_SAME)
    new.write_text(_SAME)
    context["config"] = _config(old, new)


@given("the sample OWL versions from the test data")
def _owl_versions(context):
    context["config"] = _config(
        _OWL / "ePO_sample-4.0.0.orig.ttl", _OWL / "ePO_sample-4.0.0.upd.ttl"
    )


@when("I build a version configuration pointing at a missing file")
def _build_missing(context, tmp_path):
    try:
        context["config"] = _config(tmp_path / "nope-old.ttl", tmp_path / "nope-new.ttl")
    except Exception as exception:
        context["error"] = exception


@when(parsers.parse("I load and diff them with the {engine} engine"))
def _load_diff(context, engine):
    context["result"] = VersionStoreLoader(_ENGINES[engine]()).run(context["config"])


@then(parsers.parse("the insertions count is {count:d}"))
def _insertions(context, count):
    assert context["result"].counts["v1->v2"].insertions == count


@then(parsers.parse("the deletions count is {count:d}"))
def _deletions(context, count):
    assert context["result"].counts["v1->v2"].deletions == count


@then("the total delta is greater than 0")
def _total_delta(context):
    counts = context["result"].counts["v1->v2"]
    assert counts.insertions + counts.deletions > 0


@then("a configuration error is raised")
def _config_error(context):
    from rdf_differ.loader.domain.exceptions import ConfigError

    assert isinstance(context["error"], ConfigError)
