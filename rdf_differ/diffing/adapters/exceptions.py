"""Diffing adapter exceptions (I/O / operational failures — adapters layer)."""


class FusekiException(Exception):
    """A Fuseki triple-store interaction has failed."""


class SubprocessFailure(Exception):
    """A subprocess invoked by the SKOS-history runner failed."""
