"""Typed remote-store connection settings.

``StoreSettings`` describes the **remote** SPARQL endpoint connection only —
base location, credentials, timeouts/retries. It is an **injected value object**:
the composition root (CLI / Celery task) builds it from the project ``config``
(``RDF_DIFFER_FUSEKI_*``) and passes it in; the store never reads the environment
itself. In-memory engines ignore it.

The dataset/diff shape (versions, IRIs, engine, blank-node policy) is a separate
concern carried by ``VersionStoreConfig``; the two never overlap.
"""

from pydantic import BaseModel


class StoreSettings(BaseModel):
    """Remote SPARQL endpoint connection settings (built from ``config`` by callers)."""

    location: str = "http://localhost"
    port: int = 3030
    username: str = "admin"
    password: str = ""
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_base_seconds: float = 1.0

    # Optional explicit endpoint overrides; when unset they derive from the base.
    data_endpoint_override: str | None = None
    update_endpoint_override: str | None = None
    query_endpoint_override: str | None = None

    @property
    def base_endpoint(self) -> str:
        """The ``{location}:{port}`` base the per-path endpoints derive from."""
        return f"{self.location}:{self.port}"

    @property
    def data_endpoint(self) -> str:
        """The Graph Store Protocol ``/data`` endpoint (GSP PUT/GET)."""
        return self.data_endpoint_override or f"{self.base_endpoint}/data"

    @property
    def update_endpoint(self) -> str:
        """The SPARQL 1.1 Update endpoint (POST)."""
        return self.update_endpoint_override or f"{self.base_endpoint}/update"

    @property
    def query_endpoint(self) -> str:
        """The SPARQL 1.1 Query endpoint (SELECT/ASK)."""
        return self.query_endpoint_override or f"{self.base_endpoint}/query"
