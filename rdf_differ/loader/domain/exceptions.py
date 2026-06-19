"""Loader domain exceptions (RFC: model/app-logic errors live in the domain layer).

``LoadingError`` is the family base; operational/transport failures
(``GraphStoreError``) subclass it in the adapters layer.
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
