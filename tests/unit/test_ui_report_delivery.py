"""Unit tests for the report-delivery-ux UI restoration.

Covers the new ``view_report`` (inline) and ``task_status`` (status proxy) routes,
the building-banner + poller markup on the dataset view, the View/Download action
pair in the available-reports list, and the build redirect threading the task id.

The httpx api_client is mocked; the TestClient does not follow redirects where the
redirect Location itself is the assertion target.
"""

from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

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
    page = ui.get("/create-diff")
    return BeautifulSoup(page.text, "html.parser").find("input", {"name": "csrf_token"})["value"]


def _ok(json):
    return api_client.ApiResult(status_code=200, json=json, text="")


def _err(status, detail, title="Conflict"):
    return api_client.ApiResult(
        status_code=status, json={"status": status, "title": title, "detail": detail}, text=""
    )


def _dataset(uid="uid", reports=None):
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
        "available_reports": reports if reports is not None else [],
    }


# --- build_report threads the task id into the redirect -----------------------


def test_build_report_success_redirect_carries_building_params(ui, csrf):
    with patch(f"{CLIENT}.build_report", return_value=_ok({"task_id": "t1"})):
        resp = ui.post(
            "/diffs/uid",
            data={"application_profile": "skos", "template_type": "html", "csrf_token": csrf},
            follow_redirects=False,
        )

    assert resp.status_code == 303
    location = resp.headers["location"]
    query = parse_qs(urlsplit(location).query)
    assert query["building"] == ["t1"]
    assert query["ap"] == ["skos"]
    assert query["tt"] == ["html"]


# --- view_dataset renders the building banner + poller -----------------------


def test_view_dataset_with_building_renders_banner_and_poller(ui):
    with (
        patch(f"{CLIENT}.get_dataset", return_value=_ok(_dataset())),
        patch(f"{CLIENT}.get_application_profiles", return_value=_ok([])),
    ):
        resp = ui.get("/diffs/uid?building=TASK&ap=skos&tt=html")

    assert resp.status_code == 200
    assert "Building" in resp.text
    assert "skos" in resp.text
    # The poller fetches the status endpoint for this task.
    assert "/tasks/TASK/status" in resp.text


def test_view_dataset_without_building_has_no_banner(ui):
    with (
        patch(f"{CLIENT}.get_dataset", return_value=_ok(_dataset())),
        patch(f"{CLIENT}.get_application_profiles", return_value=_ok([])),
    ):
        resp = ui.get("/diffs/uid")

    assert resp.status_code == 200
    assert "/status" not in resp.text


# --- task_status proxy -------------------------------------------------------


def test_task_status_returns_upstream_status(ui):
    with patch(f"{CLIENT}.get_task", return_value=_ok({"task_id": "t1", "status": "SUCCESS"})):
        resp = ui.get("/tasks/t1/status")

    assert resp.status_code == 200
    assert resp.json() == {"status": "SUCCESS"}


def test_task_status_degrades_to_sentinel_on_api_error(ui):
    with patch(f"{CLIENT}.get_task", return_value=_err(503, "no api")):
        resp = ui.get("/tasks/t1/status")

    # Never 500 — the poller must keep degrading gracefully.
    assert resp.status_code == 200
    assert resp.json() == {"status": "UNKNOWN"}


# --- view_report serves inline -----------------------------------------------


def test_view_report_serves_inline_sandboxed_with_pinned_media_type(ui):
    # The upstream content-type is deliberately hostile; the route must IGNORE it and
    # pin the media type by template_type, and sandbox the response (stored-XSS guard).
    response = httpx.Response(
        200,
        content=b"<html>report</html>",
        headers={"content-type": "text/html; charset=utf-8"},
        request=httpx.Request("GET", "http://api/diffs/report"),
    )
    with patch(f"{CLIENT}.get_report", return_value=response):
        resp = ui.get("/diff-report/ds/ap/html/view")

    assert resp.status_code == 200
    assert resp.content == b"<html>report</html>"
    assert "inline" in resp.headers["content-disposition"]
    assert resp.headers["content-type"].startswith("text/html")
    # hardening: sandbox CSP neutralises scripts, nosniff stops content-type sniffing
    assert "sandbox" in resp.headers["content-security-policy"]
    assert resp.headers["x-content-type-options"] == "nosniff"


def test_view_report_pins_media_type_and_does_not_trust_upstream(ui):
    # A JSON report whose upstream lies that it is text/html must be served application/json.
    response = httpx.Response(
        200,
        content=b'{"k": 1}',
        headers={"content-type": "text/html"},
        request=httpx.Request("GET", "http://api/diffs/report"),
    )
    with patch(f"{CLIENT}.get_report", return_value=response):
        resp = ui.get("/diff-report/ds/ap/json/view")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")


def test_view_report_missing_flashes_and_redirects(ui):
    response = httpx.Response(404, request=httpx.Request("GET", "http://api/diffs/report"))
    with (
        patch(f"{CLIENT}.get_report", return_value=response),
        patch(f"{CLIENT}.get_datasets", return_value=_ok([])),
    ):
        resp = ui.get("/diff-report/ds/ap/html/view")

    assert resp.status_code == 200  # followed redirect to index
    assert "Could not open the report" in resp.text


# --- available-reports list renders both View and Download -------------------


def test_available_reports_list_renders_view_and_download(ui):
    reports = [{"application_profile": "skos", "template_variations": ["html"]}]
    with (
        patch(f"{CLIENT}.get_dataset", return_value=_ok(_dataset(reports=reports))),
        patch(f"{CLIENT}.get_application_profiles", return_value=_ok([])),
    ):
        resp = ui.get("/diffs/uid")

    assert resp.status_code == 200
    soup = BeautifulSoup(resp.text, "html.parser")
    download = soup.find(id="report-uid-skos-html")
    view = soup.find(id="report-view-uid-skos-html")
    assert download is not None
    assert "/diff-report/uid/skos/html" in download["href"]
    assert view is not None
    assert view["href"].endswith("/diff-report/uid/skos/html/view")
    assert view.get("target") == "_blank"
