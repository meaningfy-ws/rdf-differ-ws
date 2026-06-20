"""Steps for rest_api.feature — FastAPI REST API journeys (EPIC behaviour-test-coverage).

Infra-free: FastAPI TestClient with services/adapters mocked.
"""

from contextlib import ExitStack, contextmanager
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when
from SPARQLWrapper.SPARQLExceptions import EndPointNotFound

from rdf_differ.api.entrypoints.api.app import app
from rdf_differ.diffing.adapters.diff_adapter import FusekiDiffAdapter

scenarios("rest_api.feature")

ROUTES = "rdf_differ.api.entrypoints.api.routes"


@contextmanager
def _fake_save_files(*_args, **_kwargs):
    yield ("/db/loc", "old.rdf", "new.rdf")


@pytest.fixture
def ctx():
    stack = ExitStack()
    state = {"client": TestClient(app), "stack": stack, "response": None}
    yield state
    stack.close()


@given(parsers.parse('the triplestore holds datasets "{first}" and "{second}"'))
def _holds(ctx, first, second):
    ctx["stack"].enter_context(
        patch.object(FusekiDiffAdapter, "list_datasets", return_value=[first, second])
    )
    ctx["stack"].enter_context(
        patch.object(
            FusekiDiffAdapter,
            "dataset_description",
            side_effect=[{"dataset_id": first}, {"dataset_id": second}],
        )
    )


@given("the triplestore has no matching dataset")
def _no_match(ctx):
    ctx["stack"].enter_context(patch(f"{ROUTES}.find_dataset_name_by_id", return_value="missing"))
    ctx["stack"].enter_context(patch(f"{ROUTES}.build_dataset_reports_location"))
    ctx["stack"].enter_context(
        patch(f"{ROUTES}.read_meta_file", return_value={"dataset_name": "missing"})
    )
    ctx["stack"].enter_context(
        patch.object(FusekiDiffAdapter, "dataset_description", side_effect=EndPointNotFound)
    )


@given("the triplestore accepts a new dataset and the queue is available")
def _accepts(ctx):
    ctx["stack"].enter_context(
        patch.object(FusekiDiffAdapter, "dataset_description", return_value={})
    )
    async_mock = ctx["stack"].enter_context(patch(f"{ROUTES}.async_create_diff"))
    async_mock.delay.return_value = MagicMock(id="task-1")
    ctx["stack"].enter_context(patch(f"{ROUTES}.push_task_to_queue"))
    ctx["stack"].enter_context(patch(f"{ROUTES}.redis_client"))
    ctx["stack"].enter_context(patch(f"{ROUTES}.save_files", _fake_save_files))


@when(parsers.parse('I GET "{path}"'))
def _get(ctx, path):
    ctx["response"] = ctx["client"].get(path)


@when(parsers.parse('I POST a valid multipart diff to "{path}"'))
def _post_diff(ctx, path):
    ctx["response"] = ctx["client"].post(
        path,
        data={
            "dataset_name": "dataset",
            "dataset_uri": "uri",
            "old_version_id": "old",
            "new_version_id": "new",
        },
        files={
            "old_version_file_content": ("old.rdf", BytesIO(b"old"), "application/rdf+xml"),
            "new_version_file_content": ("new.rdf", BytesIO(b"new"), "application/rdf+xml"),
        },
    )


@then(parsers.parse("the status is {status:d}"))
def _status(ctx, status):
    assert ctx["response"].status_code == status


@then(parsers.parse("the JSON array has {count:d} entries"))
def _array_count(ctx, count):
    assert len(ctx["response"].json()) == count


@then(parsers.parse('the problem body has title "{title}"'))
def _problem_title(ctx, title):
    assert ctx["response"].json()["title"] == title


@then(parsers.parse('the response has a "{key}"'))
def _has_key(ctx, key):
    assert key in ctx["response"].json()


@then(parsers.parse('the OpenAPI paths include "{path}"'))
def _openapi_paths(ctx, path):
    assert path in ctx["response"].json()["paths"]
