"""Browser smoke flows for the RDF Differ UI (Playwright).

Opt-in — skipped unless the `e2e` group is installed AND the UI is reachable:

    poetry install --with e2e
    poetry run playwright install chromium
    make start-services-test                      # bring up the full stack
    poetry run pytest tests/e2e --browser chromium
"""

import pytest

# Skip the whole module cleanly when pytest-playwright / the browser binding is absent,
# so a default `pytest` (no e2e group) does not error on the `page` fixture.
pytest.importorskip("playwright.sync_api")


def test_index_page_loads(page, ui_base_url):
    page.goto(f"{ui_base_url}/")
    assert page.locator("h1").first.is_visible()


def test_create_diff_page_loads(page, ui_base_url):
    page.goto(f"{ui_base_url}/create-diff")
    assert "Create" in page.content()
