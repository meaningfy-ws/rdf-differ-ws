"""Remote ``GraphStorePort`` against any SPARQL 1.1 endpoint (DEC-2, DEC-10).

Talks the Graph Store Protocol (``PUT``/``GET`` on ``/data``) for bulk graph
load/serialise, and SPARQL 1.1 Update/Query for delta writes and reads. Its
connection is **injected** as ``StoreSettings`` — it never reads the environment
itself (DIP, 12-factor). Transport/engine failures translate to
``GraphStoreError``; transient failures (timeouts, ``>=500``) are retried with
exponential backoff (``retry_attempts``/``retry_base_seconds``).
"""

import logging
import time
from collections.abc import Callable
from typing import Any, Protocol, cast
from urllib.parse import quote

import requests

from rdf_differ.config import RDF_DIFFER_LOGGER
from rdf_differ.core.adapters.sparql import SPARQLRunner
from rdf_differ.loader.adapters.graph_store import GraphStoreError
from rdf_differ.loader.adapters.settings import StoreSettings

logger = logging.getLogger(RDF_DIFFER_LOGGER)

_TRANSIENT_STATUS_FLOOR = 500


class _HttpClient(Protocol):
    """The slice of ``requests`` this adapter needs (for injection/testing)."""

    def put(self, url: str, **kwargs: Any) -> Any: ...

    def get(self, url: str, **kwargs: Any) -> Any: ...


class _SparqlClient(Protocol):
    """The slice of ``SPARQLRunner`` this adapter needs (for injection/testing)."""

    def execute(self, endpoint_url: str, query_text: str) -> dict: ...

    def execute_update(
        self,
        endpoint_url: str,
        query_text: str,
        login: str | None = None,
        password: str | None = None,
    ) -> bytes: ...


class RemoteSparqlStore:
    """A ``GraphStorePort`` over a remote SPARQL 1.1 + Graph Store Protocol endpoint."""

    def __init__(
        self,
        settings: StoreSettings,
        *,
        http_client: _HttpClient | None = None,
        sparql_client: _SparqlClient | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._http = http_client or requests
        self._sparql = sparql_client or SPARQLRunner()
        self._sleep = sleep

    def put_graph(self, graph_iri: str, data: bytes, content_type: str) -> None:
        url = f"{self._settings.data_endpoint}?graph={quote(graph_iri, safe='')}"
        headers = {"Content-Type": content_type}
        self._with_retry(
            lambda: self._http.put(url, data=data, headers=headers, timeout=self._settings.timeout),
            what=f"PUT graph <{graph_iri}>",
        )

    def clear_graph(self, graph_iri: str) -> None:
        self.update(f"CLEAR SILENT GRAPH <{graph_iri}>")

    def update(self, sparql_update: str) -> None:
        self._sparql.execute_update(
            self._settings.update_endpoint,
            sparql_update,
            login=self._settings.username,
            password=self._settings.password,
        )

    def query(self, sparql_query: str) -> dict:
        return self._sparql.execute(self._settings.query_endpoint, sparql_query)

    def serialize(self, graph_iri: str, content_type: str = "text/turtle") -> bytes:
        url = f"{self._settings.data_endpoint}?graph={quote(graph_iri, safe='')}"
        headers = {"Accept": content_type}
        response = self._with_retry(
            lambda: self._http.get(url, headers=headers, timeout=self._settings.timeout),
            what=f"GET graph <{graph_iri}>",
        )
        return cast(bytes, response.content)

    # --- transport helpers --------------------------------------------------------
    def _with_retry(self, call: Callable[[], Any], *, what: str) -> Any:
        attempts = max(1, self._settings.retry_attempts)
        last_exc: Exception | None = None
        for attempt in range(attempts):
            try:
                response = call()
                self._raise_for_status(response, what)
                return response
            except GraphStoreError as exc:
                last_exc = exc
                if not self._is_transient(response_status(exc)) or attempt == attempts - 1:
                    raise
            except requests.exceptions.RequestException as exc:
                # Timeouts/connection errors are transient by nature.
                last_exc = GraphStoreError(f"{what} failed: {exc}")
                if attempt == attempts - 1:
                    raise last_exc from exc
            self._backoff(attempt)
        # Unreachable, but keeps the type checker honest.
        raise last_exc or GraphStoreError(f"{what} failed")

    def _raise_for_status(self, response: Any, what: str) -> None:
        status = int(getattr(response, "status_code", 0))
        if status >= 400:
            body = getattr(response, "text", "")
            error = GraphStoreError(f"{what}: {status} {body}")
            error.status = status
            raise error

    def _is_transient(self, status: int | None) -> bool:
        return status is not None and status >= _TRANSIENT_STATUS_FLOOR

    def _backoff(self, attempt: int) -> None:
        delay = self._settings.retry_base_seconds * (2**attempt)
        self._sleep(delay)


def response_status(exc: GraphStoreError) -> int | None:
    """The HTTP status carried on a ``GraphStoreError``, if any."""
    return getattr(exc, "status", None)
