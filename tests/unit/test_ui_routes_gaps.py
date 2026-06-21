"""Additional unit tests for the FastAPI web UI routes, covering gaps left by
``test_ui_routes.py``: CSRF enforcement on the remaining POST routes, the
build_report happy/failure paths, API-error branches on the tasks pages, the
download_report filename derivation, and graceful degradation when fetching
application profiles fails.

The httpx api_client is mocked; the TestClient follows redirects so the final
rendered page (and its flash) is asserted.
"""

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


def _dataset(uid="uid"):
    return {
        "uid": uid,
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


def test_build_report_without_csrf_is_rejected(ui):
    """POST /diffs/{id} with a complete report form but no csrf_token returns 403."""
    resp = ui.post(
        "/diffs/uid", data={"application_profile": "ap", "template_type": "tt"}
    )  # no csrf

    assert resp.status_code == 403


def test_revoke_task_without_csrf_is_rejected(ui):
    """POST /revoke-task/{id} without a csrf_token returns 403."""
    resp = ui.post("/revoke-task/t1")  # no csrf

    assert resp.status_code == 403


def test_create_diff_wrong_csrf_token_is_rejected(ui, csrf):
    """A csrf_token that differs from the session token is rejected with 403."""
    assert csrf  # the session token is seeded by the fixture

    resp = ui.post("/create-diff", data={"csrf_token": csrf + "tampered"})

    assert resp.status_code == 403


def test_build_report_success_redirects_to_dataset_with_flash(ui, csrf):
    """A successful build enqueues the report and the dataset view shows a success flash."""
    with (
        patch(f"{CLIENT}.build_report", return_value=_ok({"task_id": "t1"})),
        patch(f"{CLIENT}.get_dataset", return_value=_ok(_dataset())),
        patch(f"{CLIENT}.get_application_profiles", return_value=_ok([])),
    ):
        resp = ui.post(
            "/diffs/uid",
            data={"application_profile": "ap", "template_type": "tt", "csrf_token": csrf},
        )

    assert resp.status_code == 200
    assert "Report building started" in resp.text
    assert "dataset_one" in BeautifulSoup(resp.text, "html.parser").find("h1").get_text()


def test_build_report_failure_redirects_to_dataset_with_error_flash(ui, csrf):
    """A failed build redirects to the dataset view, which shows the API error flash."""
    with (
        patch(f"{CLIENT}.build_report", return_value=_err(409, "Report already building.")),
        patch(f"{CLIENT}.get_dataset", return_value=_ok(_dataset())),
        patch(f"{CLIENT}.get_application_profiles", return_value=_ok([])),
    ):
        resp = ui.post(
            "/diffs/uid",
            data={"application_profile": "ap", "template_type": "tt", "csrf_token": csrf},
        )

    assert resp.status_code == 200
    assert "Report already building." in resp.text


def test_get_active_tasks_api_error_renders_with_flash_and_no_rows(ui):
    """When the API errors, GET /tasks still renders 200 with an error flash and no task rows."""
    with patch(
        f"{CLIENT}.get_active_tasks", return_value=_err(500, "boom", "Internal Server Error")
    ):
        resp = ui.get("/tasks")

    assert resp.status_code == 200
    assert "Detail: boom" in resp.text
    soup = BeautifulSoup(resp.text, "html.parser")
    body = soup.find("tbody")
    assert body is None or body.find_all("tr") == []


def test_revoke_task_error_branch_shows_error_flash(ui, csrf):
    """A failed revoke surfaces the API error flash on the redirected tasks page."""
    error = api_client.ApiResult(status_code=404, json=None, text="Unknown task.")
    with (
        patch(f"{CLIENT}.revoke_task", return_value=error),
        patch(f"{CLIENT}.get_active_tasks", return_value=_ok([])),
    ):
        resp = ui.post("/revoke-task/t1", data={"csrf_token": csrf})

    assert resp.status_code == 200
    assert "Unknown task." in resp.text


def test_download_report_filename_uses_pdf_extension_from_disposition(ui):
    """The downloaded filename derives its extension from the API's content-disposition."""
    response = httpx.Response(
        200,
        content=b"x",
        headers={"content-disposition": 'attachment; filename="r.pdf"'},
        request=httpx.Request("GET", "http://api/diffs/report"),
    )
    with patch(f"{CLIENT}.get_report", return_value=response):
        resp = ui.get("/diff-report/ds/ap/tt")

    assert resp.status_code == 200
    assert 'filename="report-ds-ap-tt.pdf"' in resp.headers["content-disposition"]


def test_download_report_filename_defaults_to_html_without_disposition(ui):
    """With no content-disposition the filename defaults to a .html extension."""
    response = httpx.Response(
        200, content=b"x", request=httpx.Request("GET", "http://api/diffs/report")
    )
    with patch(f"{CLIENT}.get_report", return_value=response):
        resp = ui.get("/diff-report/ds/ap/tt")

    assert resp.status_code == 200
    assert 'filename="report-ds-ap-tt.html"' in resp.headers["content-disposition"]


def test_view_dataset_renders_when_application_profiles_fails(ui):
    """The dataset page still renders 200 if fetching application profiles errors."""
    with (
        patch(f"{CLIENT}.get_dataset", return_value=_ok(_dataset())),
        patch(
            f"{CLIENT}.get_application_profiles",
            return_value=_err(500, "boom", "Internal Server Error"),
        ),
    ):
        resp = ui.get("/diffs/uid")

    assert resp.status_code == 200
    assert "dataset_one" in BeautifulSoup(resp.text, "html.parser").find("h1").get_text()
