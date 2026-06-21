"""Tests for issues #134 (timeout returns control) and #133 (endpoint probe)."""

import threading
import time

import pytest

from rdf_differ.diffing.entrypoints import query_profiler
from rdf_differ.diffing.entrypoints.query_profiler import (
    check_endpoint_reachable,
    main,
    run_queries,
)


def test_run_queries_returns_immediately_on_timeout_for_hung_query(tmp_path):
    """#134: a query that never returns must not block run_queries past the timeout.

    The current `with ThreadPoolExecutor(...)` block calls shutdown(wait=True) on
    exit, which blocks until the hung thread finishes. This test pins the contract
    that control returns promptly with a TIMEOUT status.
    """

    query_file = tmp_path / "hung.rq"
    query_file.write_text("SELECT * WHERE { ?s ?p ?o }", encoding="utf-8")

    release = threading.Event()

    def hung_execute(_query_text: str) -> None:
        # Block until the test explicitly releases the orphan thread (teardown),
        # never on its own.
        release.wait()

    try:
        start = time.perf_counter()
        results = run_queries(
            [query_file],
            hung_execute,
            timeout=0.2,
            printer=lambda _m: None,
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"run_queries blocked for {elapsed:.2f}s on a hung query"
        assert len(results) == 1
        assert results[0].status == "TIMEOUT"
        assert results[0].duration is None
    finally:
        # Let the orphan thread exit cleanly so it does not wedge pytest.
        release.set()


class _StubAdapter:
    """Minimal adapter stub recording whether queries were executed."""

    def __init__(self):
        self.executed_queries = []

    def list_datasets(self):
        return ["example"]

    def create_dataset(self, dataset_name):  # pragma: no cover - not reached
        return True

    def execute_query(self, dataset_name, sparql_query):  # pragma: no cover
        self.executed_queries.append(sparql_query)
        return {}


@pytest.fixture
def profile_with_query(tmp_path, monkeypatch):
    """Create a discoverable profile with one query and point config at it."""

    queries_dir = tmp_path / "example" / "queries"
    queries_dir.mkdir(parents=True)
    (queries_dir / "a.rq").write_text("SELECT * WHERE { ?s ?p ?o }", encoding="utf-8")
    monkeypatch.setenv("RDF_DIFFER_TEMPLATE_LOCATION", str(tmp_path))
    return tmp_path


def test_main_exits_non_zero_when_endpoint_unreachable(profile_with_query, monkeypatch):
    """#133: when the Fuseki endpoint is unreachable, main() must fail fast.

    No dataset work and no query execution may happen.
    """

    stub = _StubAdapter()
    monkeypatch.setattr(query_profiler, "FusekiDiffAdapter", lambda *_a, **_k: stub)
    monkeypatch.setattr(query_profiler, "check_endpoint_reachable", lambda _endpoint: False)

    exit_code = main(["example", "--endpoint", "http://fuseki.invalid"])

    assert exit_code != 0
    assert stub.executed_queries == []


def test_check_endpoint_reachable_true_on_2xx(monkeypatch):
    class _Resp:
        status_code = 200

    monkeypatch.setattr(query_profiler.requests, "get", lambda *_a, **_k: _Resp())
    assert check_endpoint_reachable("http://fuseki.test") is True


def test_check_endpoint_reachable_false_on_exception(monkeypatch):
    def _boom(*_a, **_k):
        raise query_profiler.requests.RequestException("down")

    monkeypatch.setattr(query_profiler.requests, "get", _boom)
    assert check_endpoint_reachable("http://fuseki.test") is False
