"""Domain exceptions for the RDF Loading Module.

Pure domain — no I/O. ``GraphStoreError`` (transport/engine failures) is defined
next to the port in the adapters layer; it subclasses ``LoadingError`` so callers
can catch the whole family uniformly.
"""


class LoadingError(Exception):
    """Base class for all RDF Loading Module errors."""


class ConfigError(LoadingError):
    """The loading configuration is invalid (caught before any write)."""


class UnsupportedFormatError(LoadingError):
    """A version file uses an unknown/unsupported RDF serialisation."""


class GraphLoadError(LoadingError):
    """A version file could not be parsed/loaded into a graph."""


class ValidationError(LoadingError):
    """Post-load structural or delta-content validation failed."""
