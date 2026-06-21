"""Unit tests for the FastAPI + Jinja2 web UI routes.

The httpx api_client is mocked (returning ApiResult / httpx.Response); these tests cover
rendering, form validation, flash-on-error and redirects. Replaces the Flask view tests.
"""

from io import BytesIO
from unittest.mock import patch

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from rdf_differ.api.entrypoints.ui import api_client
from rdf_differ.api.entrypoints.ui.app import app

CLIENT = "rdf_differ.api.entrypoints.ui.api_client"


@pytest.fixture
def ui():
    return TestClient(app)


@pytest.fixture
def csrf(ui):
    """A valid CSRF token bound to this client's session (seeded via the form page)."""
    page = ui.get("/create-diff")
    return BeautifulSoup(page.text, "html.parser").find("input", {"name": "csrf_token"})["value"]


def _ok(json):
    return api_client.ApiResult(status_code=200, json=json, text="")


def _err(status, detail, title="Conflict"):
    return api_client.ApiResult(
        status_code=status, json={"status": status, "title": title, "detail": detail}, text=""
    )


def _form_files():
    return {
        "old_version_file_content": ("old.rdf", BytesIO(b"old"), "application/rdf+xml"),
        "new_version_file_content": ("new.rdf", BytesIO(b"new"), "application/rdf+xml"),
    }


def _form_data(name="dataset_name"):
    return {
        "dataset_name": name,
        "dataset_description": "desc",
        "dataset_uri": "http://dataset.uri",
        "old_version_id": "old",
        "new_version_id": "new",
    }


def test_index_lists_datasets(ui):
    datasets = [{"uid": "u1", "original_name": "ds1"}, {"uid": "u2", "original_name": "ds2"}]
    with patch(f"{CLIENT}.get_datasets", return_value=_ok(datasets)):
        resp = ui.get("/")

    assert resp.status_code == 200
    soup = BeautifulSoup(resp.text, "html.parser")
    assert "Calculated diffs" in soup.find("h1").get_text()
    rows = soup.find("tbody").find_all("tr")
    assert len(rows) == 2
    assert "ds1" in rows[0].get_text()


def test_index_flashes_on_api_error(ui):
    with patch(f"{CLIENT}.get_datasets", return_value=_err(500, "boom", "Internal Server Error")):
        resp = ui.get("/")

    assert resp.status_code == 200
    assert "Detail: boom" in resp.text


def test_create_diff_invalid_name_rerenders_with_error(ui, csrf):
    resp = ui.post(
        "/create-diff", data=_form_data(name="bad name") | {"csrf_token": csrf}, files=_form_files()
    )

    assert resp.status_code == 200
    assert "Dataset name can contain only letters, numbers, _, :, and -" in resp.text


def test_create_diff_missing_file_rerenders_with_error(ui, csrf):
    resp = ui.post("/create-diff", data=_form_data() | {"csrf_token": csrf})  # no files

    assert resp.status_code == 200
    assert "A file is required" in resp.text


def test_create_diff_missing_csrf_is_rejected(ui):
    resp = ui.post("/create-diff", data=_form_data(), files=_form_files())  # no csrf

    assert resp.status_code == 403


def test_create_diff_api_conflict_shows_flash(ui, csrf):
    with patch(f"{CLIENT}.create_diff", return_value=_err(409, "Dataset is not empty.")):
        resp = ui.post(
            "/create-diff", data=_form_data() | {"csrf_token": csrf}, files=_form_files()
        )

    assert resp.status_code == 200
    assert "Status: 409. Title: Conflict Detail: Dataset is not empty." in resp.text


def test_create_diff_success_redirects_to_tasks(ui, csrf):
    with (
        patch(f"{CLIENT}.create_diff", return_value=_ok({"uid": "t1", "dataset_name": "x"})),
        patch(f"{CLIENT}.get_active_tasks", return_value=_ok([])),
    ):
        resp = ui.post(
            "/create-diff", data=_form_data() | {"csrf_token": csrf}, files=_form_files()
        )

    assert resp.status_code == 200
    assert "Active tasks" in resp.text


def test_view_dataset_renders_details(ui):
    dataset = {
        "uid": "uid",
        "dataset_name": "dataset_one123456",
        "original_name": "dataset_one",
        "dataset_description": "dataset_one is a dataset",
        "dataset_uri": "http://dataset.one",
        "old_version_file": "one_old.ttl",
        "new_version_file": "one_new.ttl",
        "dataset_versions": ["one_old", "one_new"],
        "version_named_graphs": ["http://one.version/one_old", "http://one.version/one_new"],
        "diff_date": "2020",
        "available_reports": [],
    }
    with (
        patch(f"{CLIENT}.get_dataset", return_value=_ok(dataset)),
        patch(f"{CLIENT}.get_application_profiles", return_value=_ok([])),
    ):
        resp = ui.get("/diffs/uid")

    assert resp.status_code == 200
    soup = BeautifulSoup(resp.text, "html.parser")
    assert "dataset_one" in soup.find("h1").get_text()
    body = soup.get_text()
    assert "dataset_one123456" in body
    assert "one.version/one_old" in body
    assert "one_new.ttl" in body


def test_view_dataset_missing_redirects_to_index(ui):
    with (
        patch(
            f"{CLIENT}.get_dataset", return_value=_err(404, "<uid> does not exist.", "Not Found")
        ),
        patch(f"{CLIENT}.get_datasets", return_value=_ok([])),
    ):
        resp = ui.get("/diffs/uid")

    assert resp.status_code == 200
    assert "Calculated diffs" in resp.text


def test_download_report_streams_content(ui):
    response = httpx.Response(
        200,
        content=b"important report",
        headers={"content-disposition": 'attachment; filename="r.html"'},
        request=httpx.Request("GET", "http://api/diffs/report"),
    )
    with patch(f"{CLIENT}.get_report", return_value=response):
        resp = ui.get("/diff-report/dataset/ap/type")

    assert resp.status_code == 200
    assert resp.content == b"important report"
    assert "attachment" in resp.headers["content-disposition"]


def test_download_report_failure_redirects_with_flash(ui):
    response = httpx.Response(404, request=httpx.Request("GET", "http://api/diffs/report"))
    with (
        patch(f"{CLIENT}.get_report", return_value=response),
        patch(f"{CLIENT}.get_datasets", return_value=_ok([])),
    ):
        resp = ui.get("/diff-report/dataset/ap/type")

    assert resp.status_code == 200
    assert "Could not download the report" in resp.text


def test_active_tasks_lists_and_revoke_redirects(ui, csrf):
    with patch(
        f"{CLIENT}.get_active_tasks", return_value=_ok([{"id": "t1", "type": "diff", "args": "x"}])
    ):
        resp = ui.get("/tasks")
    assert resp.status_code == 200
    assert "t1" in resp.text

    with (
        patch(f"{CLIENT}.revoke_task", return_value=_ok({"message": "task t1 set for revoking."})),
        patch(f"{CLIENT}.get_active_tasks", return_value=_ok([])),
    ):
        resp = ui.post("/revoke-task/t1", data={"csrf_token": csrf})
    assert resp.status_code == 200
    assert "set for revoking" in resp.text
