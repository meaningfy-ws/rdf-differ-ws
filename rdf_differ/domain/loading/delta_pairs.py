"""Delta-pair computation (which ``(old, new)`` pairs to diff).

Mirrors the second pass of ``load_versions.sh`` (``:401-431``): always the
consecutive pairs, plus — when enabled — the direct-to-current pairs, taking care
not to duplicate the penultimate→latest pair (which is already consecutive).

Pure domain — no I/O.
"""

from collections.abc import Sequence

Pair = tuple[str, str]


def consecutive_pairs(versions: Sequence[str]) -> list[Pair]:
    """``[(v0, v1), (v1, v2), …]`` — the immediate version-to-next transitions."""
    return [(versions[i], versions[i + 1]) for i in range(len(versions) - 1)]


def direct_to_current_pairs(versions: Sequence[str]) -> list[Pair]:
    """``(vi, latest)`` for every non-latest version, excluding the penultimate.

    The penultimate→latest pair is omitted because it is already a consecutive
    pair (the script guards this with ``old != penultimate && old != latest``).
    """
    if len(versions) < 3:
        return []
    latest = versions[-1]
    penultimate = versions[-2]
    return [(v, latest) for v in versions[:-1] if v != penultimate]


def all_delta_pairs(
    versions: Sequence[str], *, compute_direct_to_current: bool = True
) -> list[Pair]:
    """Consecutive pairs, plus direct-to-current pairs when enabled.

    Order matches the script: each consecutive pair, then (optionally) the
    direct-to-current pair, interleaved per version index. Returned de-duplicated
    while preserving first-seen order.
    """
    pairs: list[Pair] = []
    seen: set[Pair] = set()

    def _add(pair: Pair) -> None:
        if pair not in seen:
            seen.add(pair)
            pairs.append(pair)

    latest = versions[-1] if versions else None
    penultimate = versions[-2] if len(versions) >= 2 else None
    for i in range(len(versions) - 1):
        old = versions[i]
        _add((old, versions[i + 1]))
        if compute_direct_to_current and old != penultimate and old != latest:
            _add((old, latest))  # type: ignore[arg-type]
    return pairs
