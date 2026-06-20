"""Steps for web_ui.feature — FastAPI UI journeys (EPIC behaviour-test-coverage).

Infra-free: FastAPI TestClient with the httpx api_client mocked.
"""

from contextlib import ExitStack
from io import BytesIO
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from rdf_differ.api.entrypoints.ui import api_client
from rdf_differ.api.entrypoints.ui.app import app

scenarios("web_ui.feature")

CLIENT = "rdf_differ.api.entrypoints.ui.api_client"


def _ok(json):
    return api_client.ApiResult(status_code=200, json=json, text="")


def _err(status, detail):
    return api_client.ApiResult(
        status_code=status, json={"status": status, "title": "Error", "detail": detail}, text=""
    )


@pytest.fixture
def ctx():
    stack = ExitStack()
    client = TestClient(app)
    state = {"client": client, "stack": stack, "response": None}
    yield state
    stack.close()


def _patch(ctx, name, **kwargs):
    ctx["stack"].enter_context(patch(f"{CLIENT}.{name}", **kwargs))


def _csrf(ctx):
    page = ctx["client"].get("/create-diff")
    return BeautifulSoup(page.text, "html.parser").find("input", {"name": "csrf_token"})["value"]


def _form(name="dataset_name"):
    return {
        "dataset_name": name,
        "dataset_uri": "http://dataset.uri",
        "old_version_id": "old",
        "new_version_id": "new",
    }


def _files():
    return {
        "old_version_file_content": ("old.rdf", BytesIO(b"old"), "application/rdf+xml"),
        "new_version_file_content": ("new.rdf", BytesIO(b"new"), "application/rdf+xml"),
    }


@given(parsers.parse('the API returns the diffs "{first}" and "{second}"'))
def _api_lists(ctx, first, second):
    _patch(
        ctx,
        "get_datasets",
        return_value=_ok(
            [{"uid": "1", "original_name": first}, {"uid": "2", "original_name": second}]
        ),
    )


@given("the API accepts the diff creation")
def _api_accepts(ctx):
    _patch(ctx, "create_diff", return_value=_ok({"uid": "t1", "dataset_name": "x"}))
    _patch(ctx, "get_active_tasks", return_value=_ok([]))


@given("the API fails to list the diffs")
def _api_fails(ctx):
    _patch(ctx, "get_datasets", return_value=_err(500, "boom"))


@when("I open the home page")
def _open_home(ctx):
    ctx["response"] = ctx["client"].get("/")


@when("I submit a valid create-diff form")
def _submit_valid(ctx):
    data = _form() | {"csrf_token": _csrf(ctx)}
    ctx["response"] = ctx["client"].post("/create-diff", data=data, files=_files())


@when(parsers.parse('I submit a create-diff form with the name "{name}"'))
def _submit_named(ctx, name):
    data = _form(name=name) | {"csrf_token": _csrf(ctx)}
    ctx["response"] = ctx["client"].post("/create-diff", data=data, files=_files())


@when("I submit a create-diff form without a CSRF token")
def _submit_no_csrf(ctx):
    ctx["response"] = ctx["client"].post("/create-diff", data=_form(), files=_files())


@then(parsers.parse('the page shows "{text}"'))
def _page_shows(ctx, text):
    assert ctx["response"].status_code == 200
    assert text in ctx["response"].text


@then("I land on the active tasks page")
def _on_tasks(ctx):
    assert ctx["response"].status_code == 200
    assert "Active tasks" in ctx["response"].text


@then("the form shows a dataset name error")
def _name_error(ctx):
    assert ctx["response"].status_code == 200
    assert "Dataset name can contain only letters, numbers, _, :, and -" in ctx["response"].text


@then(parsers.parse("the response status is {status:d}"))
def _status_is(ctx, status):
    assert ctx["response"].status_code == status


@then("the page shows an error flash")
def _error_flash(ctx):
    assert 'class="flash flash-error"' in ctx["response"].text
