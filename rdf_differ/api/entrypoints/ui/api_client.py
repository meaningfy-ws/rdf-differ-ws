"""httpx client for the REST API (EPIC api-ui-fastapi-modernization, DEC-3/DEC-8).

Replaces ``api_wrapper.py``'s bare ``requests`` calls. Every call has an explicit
timeout, returns a typed :class:`ApiResult`, guards JSON parsing, and is logged at a
status-class level — so an API error or timeout surfaces as a flash, never a UI crash.
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from rdf_differ import config
from rdf_differ.api.entrypoints._logging import level_for_status

logger = logging.getLogger(config.RDF_DIFFER_LOGGER)

# Diff creation enqueues work and returns fast; generous ceiling for large uploads.
_TIMEOUT = httpx.Timeout(60.0)
_CONNECTION_ERROR_STATUS = 503


@dataclass
class ApiResult:
    """Outcome of an API call: status, parsed JSON (or None), raw text, success flag."""

    status_code: int
    json: Any
    text: str

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def error_message(self) -> str:
        """Human-readable error built from the problem-style body, with a text fallback."""
        if isinstance(self.json, dict) and {"status", "title", "detail"} & self.json.keys():
            return (
                f"Status: {self.json.get('status')}. Title: {self.json.get('title')} "
                f"Detail: {self.json.get('detail')}"
            )
        return self.text or f"API returned status {self.status_code}"


def _url(path: str) -> str:
    return config.RDF_DIFFER_API_SERVICE + path


def _result(response: httpx.Response) -> ApiResult:
    logger.log(
        level_for_status(response.status_code),
        "%s %s -> %s",
        response.request.method,
        response.request.url,
        response.status_code,
    )
    try:
        parsed = response.json()
    except ValueError:
        parsed = None
    return ApiResult(status_code=response.status_code, json=parsed, text=response.text)


def _request(method: str, path: str, **kwargs: Any) -> ApiResult:
    try:
        response = httpx.request(method, _url(path), timeout=_TIMEOUT, **kwargs)
    except httpx.RequestError as exception:
        logger.error("%s %s -> connection error: %s", method, _url(path), exception)
        return ApiResult(
            status_code=_CONNECTION_ERROR_STATUS,
            json=None,
            text=f"Could not reach the API: {exception}",
        )
    return _result(response)


def get_datasets() -> ApiResult:
    return _request("GET", "/diffs")


def get_dataset(dataset_id: str) -> ApiResult:
    return _request("GET", f"/diffs/{dataset_id}")


def get_application_profiles() -> ApiResult:
    return _request("GET", "/aps")


def get_active_tasks() -> ApiResult:
    return _request("GET", "/tasks/active")


def revoke_task(task_id: str) -> ApiResult:
    return _request("DELETE", f"/tasks/{task_id}")


def create_diff(data: dict, files: dict) -> ApiResult:
    """POST a multipart diff-creation request. ``files`` maps field -> (name, bytes, mime)."""
    return _request("POST", "/diffs", data=data, files=files)


def build_report(dataset_id: str, application_profile: str, template_type: str) -> ApiResult:
    return _request(
        "POST",
        "/diffs/report",
        json={
            "dataset_id": dataset_id,
            "application_profile": application_profile,
            "template_type": template_type,
            "rebuild": "true",
        },
    )


def get_report(dataset_id: str, application_profile: str, template_type: str) -> httpx.Response:
    """Fetch a built report as a raw response (the caller streams bytes + filename)."""
    return httpx.get(
        _url("/diffs/report"),
        params={
            "dataset_id": dataset_id,
            "application_profile": application_profile,
            "template_type": template_type,
        },
        timeout=_TIMEOUT,
    )
