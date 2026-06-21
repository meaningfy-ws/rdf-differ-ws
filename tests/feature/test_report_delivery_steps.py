"""Steps for report_delivery.feature — viewing, downloading and tracking reports.

Infra-free: FastAPI TestClient with the httpx api_client mocked, mirroring
test_web_ui_steps.py.
"""

from contextlib import ExitStack
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from rdf_differ.api.entrypoints.ui import api_client
from rdf_differ.api.entrypoints.ui.app import app

scenarios("report_delivery.feature")

CLIENT = "rdf_differ.api.entrypoints.ui.api_client"


def _ok(json):
    return api_client.ApiResult(status_code=200, json=json, text="")


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


# --- Given -------------------------------------------------------------------


@given(
    parsers.parse('a dataset with a built "{template_type}" report for profile "{profile}"'),
    target_fixture="report",
)
def _built_report(ctx, template_type, profile):
    response = httpx.Response(
        200,
        content=b"<html>report</html>",
        headers={
            "content-type": "text/html; charset=utf-8",
            "content-disposition": 'attachment; filename="diff.html"',
        },
        request=httpx.Request("GET", "http://api/diffs/report"),
    )
    _patch(ctx, "get_report", return_value=response)
    return {"dataset_id": "ds", "profile": profile, "template_type": template_type}


@given("the API accepts a report build and returns a task id")
def _api_accepts_build(ctx):
    _patch(ctx, "build_report", return_value=_ok({"task_id": "task-1"}))


@given("a report build task that has completed successfully")
def _task_success(ctx):
    _patch(ctx, "get_task", return_value=_ok({"task_id": "task-1", "status": "SUCCESS"}))


@given("a report build task that has failed")
def _task_failed(ctx):
    _patch(ctx, "get_task", return_value=_ok({"task_id": "task-1", "status": "FAILURE"}))


@given("no report exists for the requested dataset, profile and type", target_fixture="report")
def _no_report(ctx):
    response = httpx.Response(404, request=httpx.Request("GET", "http://api/diffs/report"))
    _patch(ctx, "get_report", return_value=response)
    _patch(ctx, "get_datasets", return_value=_ok([]))
    return {"dataset_id": "ds", "profile": "skos-core-en-only", "template_type": "html"}


# --- When --------------------------------------------------------------------


@when("I open the View action for that report")
def _open_view(ctx, report):
    ctx["response"] = ctx["client"].get(
        f"/diff-report/{report['dataset_id']}/{report['profile']}/{report['template_type']}/view"
    )


@when("I open the Download action for that report")
def _open_download(ctx, report):
    ctx["response"] = ctx["client"].get(
        f"/diff-report/{report['dataset_id']}/{report['profile']}/{report['template_type']}"
    )


@when(parsers.parse('I submit a report build for profile "{profile}" and type "{template_type}"'))
def _submit_build(ctx, profile, template_type):
    csrf = _csrf(ctx)
    ctx["response"] = ctx["client"].post(
        "/diffs/ds",
        data={
            "application_profile": profile,
            "template_type": template_type,
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )


@when("the dataset view polls the task status")
def _poll_status(ctx):
    ctx["response"] = ctx["client"].get("/tasks/task-1/status")


# --- Then --------------------------------------------------------------------


@then("the report is served inline")
def _served_inline(ctx):
    assert ctx["response"].status_code == 200
    assert "inline" in ctx["response"].headers["content-disposition"]


@then("the response content type is for HTML")
def _content_type_html(ctx):
    assert ctx["response"].headers["content-type"].startswith("text/html")


@then("the response is served as an attachment")
def _served_attachment(ctx):
    assert ctx["response"].status_code == 200
    assert "attachment" in ctx["response"].headers["content-disposition"]


@then(
    parsers.parse(
        'I am taken to the dataset view with a building indicator for "{profile}" · "{template_type}"'
    )
)
def _redirect_with_building(ctx, profile, template_type):
    assert ctx["response"].status_code == 303
    query = parse_qs(urlsplit(ctx["response"].headers["location"]).query)
    assert query["building"] == ["task-1"]
    assert query["ap"] == [profile]
    assert query["tt"] == [template_type]


@then("the status endpoint reports the task as successful")
def _status_success(ctx):
    assert ctx["response"].status_code == 200
    assert ctx["response"].json() == {"status": "SUCCESS"}


@then("the status endpoint reports the task as failed")
def _status_failed(ctx):
    assert ctx["response"].status_code == 200
    assert ctx["response"].json() == {"status": "FAILURE"}


@then("I am redirected with a clear message instead of an error")
def _redirect_with_message(ctx):
    assert ctx["response"].status_code == 200  # followed redirect to index
    assert "Could not open the report" in ctx["response"].text
