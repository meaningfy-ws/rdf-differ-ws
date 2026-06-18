"""Fixtures for the browser (Playwright) E2E smoke tests.

These are opt-in: they need the full stack running (UI + API + Fuseki + Redis + Celery)
and the `e2e` dependency group + a browser installed. They auto-skip when the UI is not
reachable, so a normal `pytest` / CI unit run is unaffected.
"""

import os

import pytest
import requests

RDF_DIFFER_UI_URL = os.environ.get("RDF_DIFFER_UI_URL", "http://localhost:8030")


def _ui_reachable() -> bool:
    try:
        requests.get(RDF_DIFFER_UI_URL, timeout=2)
        return True
    except requests.RequestException:
        return False


@pytest.fixture(scope="session")
def ui_base_url() -> str:
    return RDF_DIFFER_UI_URL


@pytest.fixture(autouse=True)
def _require_running_ui():
    if not _ui_reachable():
        pytest.skip(
            f"E2E UI not reachable at {RDF_DIFFER_UI_URL} — bring up the stack first "
            "(make start-services-test)."
        )
