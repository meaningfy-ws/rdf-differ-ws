"""Additional unit tests for FastAPI REST API routes — covering paths not exercised
by ``test_api_routes.py``.

Same approach as the sibling suite: drive the routes through FastAPI's TestClient
with services/adapters mocked. Focus is on the error-mapping and response-shaping
branches (report download, upload/lookup failures, non-serialisable task results,
the generic unhandled-error handler, and the generated OpenAPI document).
"""

import os
import tempfile
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from rdf_differ.api.entrypoints.api.app import app
from rdf_differ.api.entrypoints.api.exceptions import INTERNAL_ERROR_DETAIL
from rdf_differ.diffing.adapters.diff_adapter import FusekiDiffAdapter
from rdf_differ.reporting.services.ap_manager import ApplicationProfileManager

ROUTES = "rdf_differ.api.entrypoints.api.routes"

client = TestClient(app)


@contextmanager
def _fake_save_files(*_args, **_kwargs):
    yield ("/db/loc", "old.rdf", "new.rdf")


def _files():
    return {
        "old_version_file_content": ("old.rdf", b"<a> <b> <c> .", "application/rdf+xml"),
        "new_version_file_content": ("new.rdf", b"<a> <b> <d> .", "application/rdf+xml"),
    }


def _create_form():
    return {
        "dataset_name": "dataset",
        "dataset_uri": "uri",
        "old_version_id": "old",
        "new_version_id": "new",
    }


# --- GET /diffs/report ----------------------------------------------------------


@patch(f"{ROUTES}.find_dataset_name_by_id", return_value="ds")
@patch(f"{ROUTES}.report_exists", return_value=True)
@patch.object(ApplicationProfileManager, "get_queries_dict", return_value={})
@patch.object(ApplicationProfileManager, "get_template_folder", return_value="/tmp/x")
@patch(f"{ROUTES}.get_diff", return_value={})
def test_get_report_200_streams_file(mock_diff, mock_tf, mock_q, mock_exists, mock_find):
    """A built report is streamed back as the file's bytes with a filename header."""
    payload = b"<html>report body</html>"
    fd, report_path = tempfile.mkstemp(suffix=".html")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)

        with patch(f"{ROUTES}.retrieve_report", return_value=report_path):
            resp = client.get(
                "/diffs/report",
                params={
                    "dataset_id": "d",
                    "application_profile": "ap",
                    "template_type": "tt",
                },
            )

        assert resp.status_code == 200
        assert resp.content == payload
        assert "filename" in resp.headers["content-disposition"]
        assert os.path.basename(report_path) in resp.headers["content-disposition"]
    finally:
        os.remove(report_path)


@patch.object(ApplicationProfileManager, "get_template_folder", side_effect=LookupError)
@patch(f"{ROUTES}.get_diff", return_value={})
def test_get_report_422_on_lookup_error(mock_diff, mock_tf):
    """An unknown application profile / template (LookupError) maps to 422."""
    resp = client.get(
        "/diffs/report",
        params={"dataset_id": "d", "application_profile": "ap", "template_type": "tt"},
    )

    assert resp.status_code == 422
    assert resp.json()["title"] == "Unprocessable Entity"


# --- POST /diffs ----------------------------------------------------------------


@patch(f"{ROUTES}.redis_client")
@patch(f"{ROUTES}.push_task_to_queue")
@patch(f"{ROUTES}.async_create_diff")
@patch.object(FusekiDiffAdapter, "dataset_description", return_value={})
def test_create_diff_500_when_save_files_fails(mock_desc, mock_async, mock_push, mock_redis):
    """A ValueError while persisting the uploaded files maps to a 500."""
    with patch(f"{ROUTES}.save_files", side_effect=ValueError("disk full")):
        resp = client.post("/diffs", data=_create_form(), files=_files())

    assert resp.status_code == 500
    assert "Internal error while uploading" in resp.json()["detail"]


# --- GET /diffs/{id} ------------------------------------------------------------


@patch(f"{ROUTES}.build_dataset_reports_location")
@patch(f"{ROUTES}.find_dataset_name_by_id", return_value="dataset")
@patch(f"{ROUTES}.read_meta_file", return_value={"dataset_name": "dataset"})
@patch.object(FusekiDiffAdapter, "dataset_description", side_effect=ValueError("bad"))
def test_get_diff_500_on_value_error(mock_desc, mock_meta, mock_find, mock_loc):
    """A ValueError from the adapter (after meta is read) maps to a 500."""
    resp = client.get("/diffs/dataset")

    assert resp.status_code == 500
    assert "Unexpected Error" in resp.json()["detail"]


@patch(f"{ROUTES}.build_dataset_reports_location")
@patch(f"{ROUTES}.find_dataset_name_by_id", return_value="dataset")
@patch(f"{ROUTES}.read_meta_file", side_effect=FileNotFoundError)
def test_get_diff_404_when_meta_missing(mock_meta, mock_find, mock_loc):
    """A failure reading the meta file maps to a 404 for the dataset."""
    resp = client.get("/diffs/dataset")

    assert resp.status_code == 404


# --- GET /tasks/{id} ------------------------------------------------------------


@patch(f"{ROUTES}.retrieve_task")
def test_get_task_status_non_serialisable_result(mock_retrieve):
    """A task whose .result is not JSON-serialisable yields an empty result string."""
    mock_retrieve.return_value = MagicMock(id="t1", status="SUCCESS", result=object())

    resp = client.get("/tasks/t1")

    assert resp.status_code == 200
    assert resp.json()["result"] == ""


# --- generic unhandled error ----------------------------------------------------


def test_unhandled_error_returns_generic_500_without_leaking_internals():
    """A bare Exception escaping a route is mapped to a generic 500 problem body
    that exposes only the canonical internal-error detail, never the cause."""
    safe_client = TestClient(app, raise_server_exceptions=False)
    with patch(
        f"{ROUTES}.ApplicationProfileManager",
        side_effect=Exception("boom — secret internals"),
    ):
        resp = safe_client.get("/aps")

    assert resp.status_code == 500
    body = resp.json()
    assert body["title"] == "Internal Server Error"
    assert body["detail"] == INTERNAL_ERROR_DETAIL
    assert "boom" not in body["detail"]


# --- OpenAPI document -----------------------------------------------------------


def test_openapi_document_exposes_known_paths():
    """The generated OpenAPI document advertises the public API paths."""
    resp = client.get("/openapi.json")

    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert "/diffs" in paths
    assert "/diffs/report" in paths
    assert "/tasks/active" in paths


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
