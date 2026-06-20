"""Diffing domain exceptions (dataset/version invariants — domain layer)."""


class VersionMissing(Exception):
    """A required dataset version does not exist."""


class VersionExists(Exception):
    """A dataset version with the same id already exists."""


class VersionsDeltaExists(Exception):
    """A delta for the given version pair already exists."""
