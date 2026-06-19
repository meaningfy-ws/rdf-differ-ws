"""The loader domain model — pure value objects, enums, and rules (no I/O).

One cohesive module for the loader's domain (mirroring the project's single-file
``domain/model.py`` convention): the error hierarchy, the engine/blank-node enums
and the blank-node strategy seam, the self-validating ``VersionStoreConfig`` and
its helpers, the result value objects, and the delta-pair computation. It imports
nothing upward and no I/O framework.
"""

from collections.abc import Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
    field_validator,
    model_validator,
)
from pydantic import (
    ValidationError as PydanticValidationError,
)

from rdf_differ.loader.domain.exceptions import ConfigError


# --- enums --------------------------------------------------------------------
class Engine(StrEnum):
    """Which ``GraphStorePort`` backend to use."""

    REMOTE = "remote"
    OXIGRAPH = "oxigraph"
    RDFLIB = "rdflib"


class BlankNodePolicy(StrEnum):
    """How blank nodes participate in deltas."""

    EXCLUDE = "exclude"
    DOCUMENT_ONLY = "document_only"
    SKOLEMISE = "skolemise"


# --- blank-node strategy seam (DEC-9) -----------------------------------------
@runtime_checkable
class BlankNodeStrategy(Protocol):
    """Transforms parsed RDF *before* it is loaded into a graph store.

    Engine-agnostic: it operates on serialised RDF bytes, so it applies equally
    to the in-memory and remote stores. The transform must be deterministic. The
    rdflib-backed ``SKOLEMISE`` implementation lives in the adapters layer.
    """

    policy: BlankNodePolicy

    def transform(self, data: bytes, *, content_type: str, base_iri: str) -> bytes:
        """Return the (possibly rewritten) RDF for loading."""
        ...


class IdentityBlankNodeStrategy:
    """No-op strategy for ``EXCLUDE`` / ``DOCUMENT_ONLY`` (pure, no rdflib).

    Filtering for ``EXCLUDE`` happens in the delta SPARQL templates, not here, so
    the bytes are returned unchanged.
    """

    policy: BlankNodePolicy

    def __init__(self, policy: BlankNodePolicy = BlankNodePolicy.EXCLUDE) -> None:
        if policy is BlankNodePolicy.SKOLEMISE:
            raise ValueError(
                "IdentityBlankNodeStrategy does not handle SKOLEMISE; "
                "use the rdflib skolemiser in the adapters layer"
            )
        self.policy = policy

    def transform(self, data: bytes, *, content_type: str, base_iri: str) -> bytes:
        return data


# --- configuration (DEC-3, pydantic v2) ---------------------------------------
def _is_absolute_iri(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme) and bool(parsed.netloc)


class VersionSpec(BaseModel):
    """One vocabulary version: its id, source file, and optional metadata."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    file: FilePath
    date: str | None = None
    identifier: str | None = None
    description: str | None = None


class VersionStoreConfig(BaseModel):
    """The full, validated shape of a load/diff request.

    Describes the dataset/diff shape only — versions, IRIs, engine, blank-node
    policy. Environment-independent: it carries no endpoint or credentials; the
    store connection is a separate ``StoreSettings`` concern (DEC-10).
    """

    model_config = ConfigDict(frozen=True)

    dataset_id: str = Field(min_length=1)
    scheme_uri: str
    base_version_iri: str | None = None
    engine: Engine = Engine.REMOTE
    blank_node_policy: BlankNodePolicy = BlankNodePolicy.EXCLUDE
    compute_direct_to_current: bool = True
    versions: list[VersionSpec]
    in_memory_max_mb: int = 512
    retry_attempts: int = 3
    retry_base_seconds: float = 1.0

    @field_validator("scheme_uri")
    @classmethod
    def _scheme_uri_absolute(cls, value: str) -> str:
        if not _is_absolute_iri(value):
            raise ValueError("scheme URI must be an absolute IRI")
        return value

    @field_validator("base_version_iri")
    @classmethod
    def _base_iri_absolute(cls, value: str | None) -> str | None:
        if value is not None and not _is_absolute_iri(value):
            raise ValueError("base version IRI must be an absolute IRI")
        return value

    @field_validator("versions")
    @classmethod
    def _at_least_two(cls, value: list[VersionSpec]) -> list[VersionSpec]:
        if len(value) < 2:
            raise ValueError("at least two versions are required")
        return value

    @model_validator(mode="after")
    def _unique_ids_and_one_format(self) -> "VersionStoreConfig":
        ids = [v.id for v in self.versions]
        if len(ids) != len(set(ids)):
            raise ValueError("version identifiers must be unique")
        suffixes = {Path(str(v.file)).suffix.lower() for v in self.versions}
        if len(suffixes) > 1:
            raise ValueError("all version files must share one format")
        return self

    @property
    def version_ids(self) -> list[str]:
        return [v.id for v in self.versions]

    @property
    def current_version(self) -> str:
        return self.versions[-1].id


def build_version_store_config(data: Mapping[str, Any]) -> VersionStoreConfig:
    """Construct a ``VersionStoreConfig``, surfacing failures as ``ConfigError``.

    Entrypoints/services should use this rather than the raw constructor so that a
    bad config is reported with a single, user-facing reason and exits cleanly.
    """
    try:
        return VersionStoreConfig.model_validate(dict(data))
    except PydanticValidationError as exc:
        reasons = "; ".join(_format_error(err) for err in exc.errors())
        raise ConfigError(reasons) from exc


def _format_error(err: Mapping[str, Any]) -> str:
    loc = ".".join(str(p) for p in err.get("loc", ()))
    msg = err.get("msg", "invalid value")
    # pydantic prefixes custom ValueError messages with "Value error, "
    msg = msg.removeprefix("Value error, ")
    return f"{loc}: {msg}" if loc else msg


class ResolvedVersionMeta(BaseModel):
    """The identifier/date finally used for a version after resolution."""

    model_config = ConfigDict(frozen=True)

    identifier: str
    date: str | None = None


def resolve_version_meta(
    spec: VersionSpec,
    *,
    data_identifier: str | None = None,
    data_date: str | None = None,
) -> ResolvedVersionMeta:
    """Resolve a version's identifier/date — data wins, then config, then id.

    Precedence (F7/F14, replacing the script's ``agrovoc jel`` hack):
      * identifier: data → config (`spec.identifier`) → the version id;
      * date:       data → config (`spec.date`) → ``None``.
    """
    identifier = data_identifier or spec.identifier or spec.id
    date = data_date or spec.date or None
    return ResolvedVersionMeta(identifier=identifier, date=date)


# --- results ------------------------------------------------------------------
class DeltaCounts(BaseModel):
    model_config = ConfigDict(frozen=True)

    insertions: int
    deletions: int


class LoadResult(BaseModel):
    """The machine-readable outcome of a load/diff run."""

    model_config = ConfigDict(frozen=True)

    dataset_id: str
    current_version: str
    delta_pairs: list[tuple[str, str]]
    counts: dict[str, DeltaCounts]
    validation: str = "passed"

    @staticmethod
    def pair_key(old: str, new: str) -> str:
        return f"{old}->{new}"


# --- delta-pair computation ---------------------------------------------------
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
