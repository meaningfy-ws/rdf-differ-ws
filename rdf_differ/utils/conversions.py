"""Small value-conversion helpers (utils layer)."""

_TRUE_VALUES = {"1", "true", "yes", "y", "on", "t"}


def strtobool(value: str) -> bool:
    """Parse a truthy string to a bool.

    Drop-in replacement for the removed ``distutils.util.strtobool`` (gone in Python 3.12),
    returning a ``bool`` instead of ``int``. Unrecognised values are treated as False.
    """
    return str(value).strip().lower() in _TRUE_VALUES
