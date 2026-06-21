"""Additional unit tests for the UI's httpx API client, covering gaps left by
``test_ui_api_client.py``: the get_report connection guard (degrade to 503 rather
than raise) and the ApiResult.error_message text/status fallbacks.
"""

from unittest.mock import patch

import httpx

from rdf_differ.api.entrypoints.ui import api_client

CLIENT = "rdf_differ.api.entrypoints.ui.api_client.httpx"


def test_get_report_connection_error_returns_503_response():
    """A connection error in get_report degrades to a 503 Response, never an exception."""
    with patch(f"{CLIENT}.get", side_effect=httpx.ConnectError("down")):
        response = api_client.get_report("d", "ap", "tt")

    assert isinstance(response, httpx.Response)
    assert response.status_code == 503


def test_error_message_falls_back_to_raw_text():
    """Without a problem-style body, error_message returns the raw response text."""
    result = api_client.ApiResult(status_code=406, json={"message": "x"}, text="raw text")

    assert result.error_message() == "raw text"


def test_error_message_falls_back_to_status_when_empty():
    """With neither a problem body nor text, error_message mentions the status code."""
    result = api_client.ApiResult(status_code=502, json=None, text="")

    message = result.error_message()
    assert message
    assert "502" in message
