"""Typed remote-store connection settings (DEC-10).

``StoreSettings`` describes the **remote** SPARQL endpoint connection only —
base location, credentials, timeouts/retries — read from the environment
(``RDF_DIFFER_FUSEKI_*``, mirroring ``config.py``). It is an I/O concern, so it
lives in the adapters layer, never in ``domain``. In-memory engines ignore it.

The dataset/diff shape (versions, IRIs, engine, blank-node policy) is a separate
concern carried by ``VersionStoreConfig`` (DEC-3); the two never overlap.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class StoreSettings(BaseSettings):
    """Remote SPARQL endpoint connection settings (env ``RDF_DIFFER_FUSEKI_*``)."""

    model_config = SettingsConfigDict(env_prefix="RDF_DIFFER_FUSEKI_", extra="ignore")

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
