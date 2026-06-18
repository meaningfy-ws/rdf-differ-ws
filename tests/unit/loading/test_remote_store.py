"""Unit tests for ``RemoteSparqlStore`` with fake HTTP/SPARQL clients (no network)."""

import pytest
import requests

from rdf_differ.adapters.loading.graph_store_port import GraphStoreError, GraphStorePort
from rdf_differ.adapters.loading.remote_store import RemoteSparqlStore
from rdf_differ.adapters.loading.settings import StoreSettings

NO_SLEEP = lambda *_: None  # noqa: E731 — tiny test helper


class FakeResponse:
    def __init__(self, status_code: int = 200, text: str = "", content: bytes = b""):
        self.status_code = status_code
        self.text = text
        self.content = content


class FakeHttpClient:
    def __init__(self, responses=None):
        self._responses = list(responses or [FakeResponse()])
        self.put_calls = []
        self.get_calls = []

    def _next(self):
        return self._responses.pop(0) if self._responses else FakeResponse()

    def put(self, url, **kwargs):
        self.put_calls.append((url, kwargs))
        return self._next()

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return self._next()


class FakeSparqlClient:
    def __init__(self, query_result=None):
        self._query_result = query_result or {"head": {}, "boolean": True}
        self.update_calls = []
        self.query_calls = []

    def execute(self, endpoint_url, query_text):
        self.query_calls.append((endpoint_url, query_text))
        return self._query_result

    def execute_update(self, endpoint_url, query_text, login=None, password=None):
        self.update_calls.append((endpoint_url, query_text, login, password))
        return b""


def _settings(**overrides) -> StoreSettings:
    base = {"location": "http://store", "port": 3030, "username": "admin", "password": "pw"}
    base.update(overrides)
    return StoreSettings(**base)


def _store(http=None, sparql=None, settings=None) -> RemoteSparqlStore:
    return RemoteSparqlStore(
        settings or _settings(),
        http_client=http or FakeHttpClient(),
        sparql_client=sparql or FakeSparqlClient(),
        sleep=NO_SLEEP,
    )


def test_is_a_graph_store_port():
    assert isinstance(_store(), GraphStorePort)


def test_put_graph_issues_put_to_data_endpoint_with_graph_and_content_type():
    http = FakeHttpClient()
    store = _store(http=http)

    store.put_graph("http://ex/g1", b"<a> <b> <c> .", "text/turtle")

    url, kwargs = http.put_calls[0]
    assert url == "http://store:3030/data?graph=http%3A%2F%2Fex%2Fg1"
    assert kwargs["headers"]["Content-Type"] == "text/turtle"
    assert kwargs["data"] == b"<a> <b> <c> ."


def test_update_calls_sparql_execute_update_with_credentials():
    sparql = FakeSparqlClient()
    store = _store(sparql=sparql)

    store.update("INSERT DATA { <a> <b> <c> }")

    endpoint, query, login, password = sparql.update_calls[0]
    assert endpoint == "http://store:3030/update"
    assert query == "INSERT DATA { <a> <b> <c> }"
    assert (login, password) == ("admin", "pw")


def test_clear_graph_issues_clear_silent_update():
    sparql = FakeSparqlClient()
    store = _store(sparql=sparql)

    store.clear_graph("http://ex/g1")

    _, query, _, _ = sparql.update_calls[0]
    assert query == "CLEAR SILENT GRAPH <http://ex/g1>"


def test_query_returns_sparql_client_result():
    sparql = FakeSparqlClient(query_result={"head": {}, "boolean": False})
    store = _store(sparql=sparql)

    result = store.query("ASK { ?s ?p ?o }")

    assert result == {"head": {}, "boolean": False}
    assert sparql.query_calls[0][0] == "http://store:3030/query"


def test_serialize_gets_data_endpoint_with_accept_and_returns_bytes():
    http = FakeHttpClient([FakeResponse(content=b"<a> <b> <c> .")])
    store = _store(http=http)

    payload = store.serialize("http://ex/g1", "application/n-triples")

    url, kwargs = http.get_calls[0]
    assert url == "http://store:3030/data?graph=http%3A%2F%2Fex%2Fg1"
    assert kwargs["headers"]["Accept"] == "application/n-triples"
    assert payload == b"<a> <b> <c> ."


def test_http_status_ge_400_raises_graph_store_error_with_status_and_body():
    http = FakeHttpClient([FakeResponse(status_code=400, text="bad request")])
    store = _store(http=http)

    with pytest.raises(GraphStoreError) as exc_info:
        store.put_graph("http://ex/g1", b"data", "text/turtle")

    assert "400" in str(exc_info.value)
    assert "bad request" in str(exc_info.value)


def test_transient_503_is_retried_then_raises():
    http = FakeHttpClient([FakeResponse(status_code=503, text="busy")] * 3)
    store = _store(http=http, settings=_settings(retry_attempts=3))

    with pytest.raises(GraphStoreError):
        store.put_graph("http://ex/g1", b"data", "text/turtle")

    assert len(http.put_calls) == 3  # retried up to retry_attempts


def test_transient_503_then_success_recovers():
    http = FakeHttpClient(
        [FakeResponse(status_code=503, text="busy"), FakeResponse(status_code=200)]
    )
    store = _store(http=http, settings=_settings(retry_attempts=3))

    store.put_graph("http://ex/g1", b"data", "text/turtle")

    assert len(http.put_calls) == 2


def test_timeout_is_retried_as_transient():
    class TimingOutClient(FakeHttpClient):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def put(self, url, **kwargs):
            self.calls += 1
            raise requests.exceptions.Timeout("slow")

    http = TimingOutClient()
    store = _store(http=http, settings=_settings(retry_attempts=2))

    with pytest.raises(GraphStoreError):
        store.put_graph("http://ex/g1", b"data", "text/turtle")

    assert http.calls == 2
