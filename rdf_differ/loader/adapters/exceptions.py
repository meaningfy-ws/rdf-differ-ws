"""Loader adapter exceptions (I/O / operational failures live in the adapters layer)."""

from rdf_differ.loader.domain.exceptions import LoadingError


class GraphStoreError(LoadingError):
    """A triple-store transport/engine failure (HTTP error, parse error, …).

    ``status`` carries the HTTP status when the failure came from a remote
    endpoint (used to decide whether a retry is worthwhile); ``None`` otherwise.
    """

    status: int | None = None
