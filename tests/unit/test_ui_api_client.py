"""Unit tests for the UI's httpx API client."""

from unittest.mock import patch

import httpx

from rdf_differ.api.entrypoints.ui import api_client

CLIENT = "rdf_differ.api.entrypoints.ui.api_client.httpx"


def _response(status_code: int, *, json=None, text=None, method="GET", path="/diffs"):
    request = httpx.Request(method, f"http://api{path}")
    if json is not None:
        return httpx.Response(status_code, json=json, request=request)
    return httpx.Response(status_code, text=text or "", request=request)


def test_ok_result_parses_json():
    with patch(f"{CLIENT}.request", return_value=_response(200, json=[{"uid": "a"}])):
        result = api_client.get_datasets()

    assert result.ok
    assert result.status_code == 200
    assert result.json == [{"uid": "a"}]


def test_error_result_is_not_ok_and_formats_message():
    body = {"status": 500, "title": "Internal Server Error", "detail": "boom"}
    with patch(f"{CLIENT}.request", return_value=_response(500, json=body)):
        result = api_client.get_datasets()

    assert not result.ok
    assert result.status_code == 500
    assert "Detail: boom" in result.error_message()


def test_non_json_response_does_not_crash():
    with patch(f"{CLIENT}.request", return_value=_response(502, text="<html>bad gateway</html>")):
        result = api_client.get_dataset("d")

    assert not result.ok
    assert result.json is None
    assert "bad gateway" in result.text


def test_connection_error_becomes_503_not_an_exception():
    with patch(f"{CLIENT}.request", side_effect=httpx.ConnectError("refused")):
        result = api_client.get_datasets()

    assert not result.ok
    assert result.status_code == 503
    assert "Could not reach the API" in result.error_message()


def test_timeout_becomes_503():
    with patch(f"{CLIENT}.request", side_effect=httpx.ReadTimeout("slow")):
        result = api_client.get_active_tasks()

    assert result.status_code == 503
    assert not result.ok


def test_create_diff_passes_multipart():
    with patch(f"{CLIENT}.request", return_value=_response(200, json={"uid": "t1"})) as mock_req:
        api_client.create_diff(
            data={"dataset_name": "d"},
            files={"old_version_file_content": ("o.rdf", b"x", "application/rdf+xml")},
        )

    _, kwargs = mock_req.call_args
    assert kwargs["data"] == {"dataset_name": "d"}
    assert "old_version_file_content" in kwargs["files"]


def test_build_report_sends_rebuild_true():
    with patch(f"{CLIENT}.request", return_value=_response(200, json={"task_id": "t"})) as mock_req:
        api_client.build_report("d", "ap", "tt")

    _, kwargs = mock_req.call_args
    assert kwargs["json"]["rebuild"] == "true"
    assert kwargs["json"]["dataset_id"] == "d"
