"""Steps for loading_diff_edge_cases.feature.

These cover the loading and diff-computation behaviour with the in-memory engines
(rdflib, pyoxigraph) over small fixtures and the existing OWL/SHACL sample data — no
running triple store required.
"""

from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from rdf_differ.loader.adapters.in_memory_stores import PyoxigraphStore, RdflibStore
from rdf_differ.loader.domain.model import build_version_store_config
from rdf_differ.loader.services.loader import VersionStoreLoader, validate_store

scenarios("loading_diff_edge_cases.feature")

_ENGINES = {"oxigraph": PyoxigraphStore, "rdflib": RdflibStore}
_OWL = Path(__file__).resolve().parents[1] / "test_data" / "owl"
_SHACL = Path(__file__).resolve().parents[1] / "test_data" / "shacl"
_SAME = "@prefix ex: <http://ex/> . ex:a ex:p ex:b ."


@pytest.fixture
def context():
    return {"error": None}


def _config(old, new, policy=None):
    data = {
        "dataset_id": "ds",
        "scheme_uri": "http://example.org/scheme",
        "versions": [{"id": "v1", "file": str(old)}, {"id": "v2", "file": str(new)}],
    }
    if policy:
        data["blank_node_policy"] = policy
    return build_version_store_config(data)


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


# --- cross-engine equivalence -------------------------------------------------


@when("I load and diff them with both engines")
def _both_engines(context):
    context["both"] = {
        name: VersionStoreLoader(engine()).run(context["config"]).counts["v1->v2"]
        for name, engine in _ENGINES.items()
    }


@then("both engines report the same insertions and deletions")
def _engines_agree(context):
    rdflib_counts = context["both"]["rdflib"]
    oxigraph_counts = context["both"]["oxigraph"]
    assert rdflib_counts.insertions == oxigraph_counts.insertions
    assert rdflib_counts.deletions == oxigraph_counts.deletions


# --- three-version history ----------------------------------------------------


@given("three OWL versions where the third restores the first")
def _three_versions(context):
    original = str(_OWL / "ePO_sample-4.0.0.orig.ttl")
    updated = str(_OWL / "ePO_sample-4.0.0.upd.ttl")
    context["config"] = build_version_store_config(
        {
            "dataset_id": "ds",
            "scheme_uri": "http://example.org/scheme",
            "versions": [
                {"id": "v1", "file": original},
                {"id": "v2", "file": updated},
                {"id": "v3", "file": original},
            ],
        }
    )


@when("I load and diff the three versions with the rdflib engine")
def _load_three(context):
    context["result"] = VersionStoreLoader(RdflibStore()).run(context["config"])


@then("the v1->v2 and v2->v3 deltas are mirror images")
def _mirror_deltas(context):
    counts = context["result"].counts
    assert counts["v1->v2"].insertions == counts["v2->v3"].deletions
    assert counts["v1->v2"].deletions == counts["v2->v3"].insertions


@then("the v1->v3 delta is empty")
def _v1_v3_empty(context):
    counts = context["result"].counts["v1->v3"]
    assert counts.insertions == 0
    assert counts.deletions == 0


# --- blank-node policy effect -------------------------------------------------


@given("the sample SHACL versions from the test data")
def _shacl_versions(context):
    context["shacl"] = (
        _SHACL / "ePO_shapes_sample-4.0.0.orig.ttl",
        _SHACL / "ePO_shapes_sample-4.0.0.upd.ttl",
    )


@when("I diff them with the exclude and document_only policies")
def _diff_two_policies(context):
    old, new = context["shacl"]
    context["by_policy"] = {
        policy: VersionStoreLoader(RdflibStore()).run(_config(old, new, policy)).counts["v1->v2"]
        for policy in ("exclude", "document_only")
    }


@then("the exclude policy reports fewer changes than document_only")
def _exclude_fewer(context):
    exclude = context["by_policy"]["exclude"]
    document_only = context["by_policy"]["document_only"]
    assert (
        exclude.insertions + exclude.deletions < document_only.insertions + document_only.deletions
    )


# --- validation of an empty version ------------------------------------------


@given("a version configuration whose second version file is empty")
def _empty_second_version(context, tmp_path):
    old = tmp_path / "v1.ttl"
    old.write_text(_SAME)
    empty = tmp_path / "v2.ttl"
    empty.write_text("")
    context["config"] = _config(old, empty)


@when("I load and validate it with the rdflib engine")
def _load_and_validate(context):
    store = RdflibStore()
    try:
        VersionStoreLoader(store).run(context["config"])
        validate_store(context["config"], store)
    except Exception as exception:
        context["error"] = exception


@then("a validation error is raised")
def _validation_error(context):
    from rdf_differ.loader.domain.exceptions import ValidationError

    assert isinstance(context["error"], ValidationError)


# --- mixed file formats -------------------------------------------------------


@when("I build a version configuration mixing turtle and rdf-xml files")
def _build_mixed_formats(context, tmp_path):
    turtle = tmp_path / "v1.ttl"
    turtle.write_text(_SAME)
    rdf_xml = tmp_path / "v2.rdf"
    rdf_xml.write_text("<rdf/>")
    try:
        context["config"] = _config(turtle, rdf_xml)
    except Exception as exception:
        context["error"] = exception
