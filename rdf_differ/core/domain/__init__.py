"""Core (commons) domain — small shared helpers live here (no module needed)."""

_TRUE_VALUES = {"1", "true", "yes", "y", "on", "t"}


def strtobool(value: str) -> bool:
    """Parse a truthy string to a ``bool``.

    Drop-in replacement for the removed ``distutils.util.strtobool`` (gone in
    Python 3.12); unrecognised values are treated as ``False``.
    """
    return str(value).strip().lower() in _TRUE_VALUES
