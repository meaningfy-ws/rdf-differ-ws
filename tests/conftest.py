#!/usr/bin/python3

# conftest.py
# Date: 11/08/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

import contextlib
from collections import namedtuple
from io import BytesIO

import pytest
import requests
from werkzeug.datastructures import FileStorage

from rdf_differ import config
from rdf_differ.api.entrypoints.ui import app as ui_app
from rdf_differ.core.adapters.sparql import SPARQLRunner
from rdf_differ.diffing.adapters.diff_adapter import FusekiDiffAdapter
from rdf_differ.diffing.adapters.exceptions import FusekiException
from rdf_differ.diffing.adapters.skos_history_wrapper import SKOSHistoryRunner


class FakeSPARQLRunner:
    def __init__(self, result_format: str = "json"):
        self.return_value = {"head": {"vars": []}, "results": {"bindings": []}}

    def execute(self, endpoint_url: str, query_text: str):
        return self.return_value


@pytest.fixture(scope="function")
def fake_sparql_runner():
    return FakeSPARQLRunner("http://some.url")


RequestObj = namedtuple("RequestObj", ["status_code", "url", "text"])


class FakeRequests:
    def __init__(self):
        self.text = None
        self.status_code = None
        self.url = None

    def get(self, url, params=None, **kwargs):
        self.url = url
        return self

    def delete(self, url, **kwargs):
        self.url = url
        return self

    def post(self, url, data=None, json=None, **kwargs):
        self.url = url
        return self


class FakeRedisClient:
    def __init__(self, lrange_return: list = None):
        self.actions = list()
        self.lrange_return = lrange_return

    def lpush(self, key, value):
        self.actions.append(("LEFT PUSH", key, value))

    def lrem(self, key, count, value):
        self.actions.append(("REMOVE VALUE FROM KEY", key, count, value))
        return 1

    def lrange(self, key, start, end):
        self.actions.append(("GET LIST FROM KEY", key, start, end))
        return self.lrange_return


@pytest.fixture(scope="function")
def fake_requests():
    return FakeRequests()


def helper_create_skos_runner(
    dataset="dataset",
    scheme_uri="http://scheme.uri",
    endpoint="http://test.point",
    basedir="/basedir",
    old_version_file="old.rdf",
    new_version_file="new.rdf",
    old_version_id="v1",
    new_version_id="v2",
    filename="file",
):
    return SKOSHistoryRunner(
        dataset=dataset,
        scheme_uri=scheme_uri,
        basedir=basedir,
        filename=filename,
        endpoint=endpoint,
        old_version_file=old_version_file,
        new_version_file=new_version_file,
        old_version_id=old_version_id,
        new_version_id=new_version_id,
    )


def helper_fuseki_service(
    triplestore_service_url: str = "http://localhost:3030/",
    http_client=FakeRequests(),
    sparql_client=FakeSPARQLRunner(),
):
    return FusekiDiffAdapter(
        triplestore_service_url=triplestore_service_url,
        http_client=http_client,
        sparql_client=sparql_client,
    )


@pytest.fixture
def ui_client():
    from fastapi.testclient import TestClient

    return TestClient(ui_app)


@pytest.fixture
def live_fuseki() -> str:
    """Skip the test unless a live Fuseki is reachable.

    Lets service-dependent tests run against a plain ``docker compose up`` stack and
    skip cleanly otherwise — no special bring-up target needed.
    """
    base = config.RDF_DIFFER_FUSEKI_SERVICE
    try:
        response = requests.get(f"{base}/$/ping", timeout=2)
    except requests.RequestException:
        pytest.skip("Fuseki is not reachable")
    if response.status_code != 200:
        pytest.skip("Fuseki is not reachable")
    return base


@pytest.fixture
def subdiv_dataset(live_fuseki: str):
    """Provision (and tear down) an empty ``subdiv`` dataset on the live Fuseki.

    Replaces the old ``make _test-data-fuseki`` seeding: tests that load versions into
    ``subdiv`` now create the dataset themselves, so the stack needs no pre-seeding.
    """
    adapter = FusekiDiffAdapter(
        triplestore_service_url=config.RDF_DIFFER_FUSEKI_SERVICE,
        http_client=requests,
        sparql_client=SPARQLRunner(),
    )
    with contextlib.suppress(FusekiException):
        adapter.create_dataset("subdiv")  # already exists is fine — the test populates it
    yield "subdiv"
    with contextlib.suppress(FusekiException):
        adapter.delete_dataset("subdiv")


def helper_create_diff(file_1=None, file_2=None, body=None):
    file_1 = file_1 if file_1 else FileStorage((BytesIO(b"1")), filename="old_file.rdf")
    file_2 = file_2 if file_2 else FileStorage((BytesIO(b"2")), filename="new_file.rdf")
    body = (
        body
        if body
        else {
            "dataset_name": "dataset",
            "dataset_uri": "uri",
            "old_version_id": "old",
            "new_version_id": "new",
        }
    )
    return file_1, file_2, body


# Marker injection by path (Meaningfy convention): a test's directory decides its
# marker — never add a per-file `pytestmark`. Run a layer with e.g. `pytest -m unit`.
_MARKER_BY_DIR = ("unit", "feature", "e2e", "integration")


def pytest_collection_modifyitems(config, items):
    root = str(config.rootpath).replace("\\", "/")
    for item in items:
        # An explicit layer marker on a test wins over the directory default — lets a
        # service-dependent test under tests/unit/ opt into `integration` instead.
        if any(item.get_closest_marker(layer) for layer in _MARKER_BY_DIR):
            continue
        rel = str(item.path).replace("\\", "/").replace(root, "")
        for layer in _MARKER_BY_DIR:
            if f"/tests/{layer}/" in rel:
                item.add_marker(getattr(pytest.mark, layer))
                break
