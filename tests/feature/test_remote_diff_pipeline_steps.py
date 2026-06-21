"""Steps for remote_diff_pipeline.feature.

@integration — needs a live API (e.g. `make start-services-test`). Skipped if unreachable.
"""

import os
from pathlib import Path

import httpx
import pytest
from pytest_bdd import given, scenarios, then, when

scenarios("remote_diff_pipeline.feature")

BASE_URL = os.environ.get("RDF_DIFFER_BASE_URL", "http://localhost:4030")
_OWL = Path(__file__).resolve().parents[1] / "test_data" / "owl"


@pytest.fixture
def context():
    return {}


@given("a reachable RDF Differ API")
def _reachable(context):
    try:
        httpx.get(f"{BASE_URL}/diffs", timeout=5.0)
    except httpx.RequestError:
        pytest.skip(f"No RDF Differ API reachable at {BASE_URL}")
    context["base"] = BASE_URL


@when("I post two RDF versions to create a diff")
def _post(context):
    with (
        open(_OWL / "ePO_sample-4.0.0.orig.ttl", "rb") as old,
        open(_OWL / "ePO_sample-4.0.0.upd.ttl", "rb") as new,
    ):
        context["response"] = httpx.post(
            f"{context['base']}/diffs",
            data={
                "dataset_name": "bddsmoke",
                "dataset_uri": "http://data.europa.eu/a4g/ontology",
                "old_version_id": "v1",
                "new_version_id": "v2",
            },
            files={
                "old_version_file_content": ("old.ttl", old.read(), "text/turtle"),
                "new_version_file_content": ("new.ttl", new.read(), "text/turtle"),
            },
            timeout=60.0,
        )


@then("the API responds with a task uid")
def _task_uid(context):
    assert context["response"].status_code == 200, context["response"].text
    assert context["response"].json().get("uid")
