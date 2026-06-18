"""Typed, self-validating loading configuration (DEC-3 — pydantic v2).

The config describes the **dataset/diff shape** only — versions, IRIs, engine,
blank-node policy. It is environment-independent and carries **no endpoint or
credentials**; the store connection is a separate ``StoreSettings`` concern
(DEC-10) in the adapters layer. Invalid configurations cannot be represented:
validation runs at construction. ``build_version_store_config`` adapts pydantic's
``ValidationError`` into the domain ``ConfigError`` for callers/entrypoints.
"""

from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
    ValidationError,
    field_validator,
    model_validator,
)

from rdf_differ.domain.loading.blank_nodes import BlankNodePolicy
from rdf_differ.domain.loading.errors import ConfigError


class Engine(StrEnum):
    """Which ``GraphStorePort`` backend to use."""

    REMOTE = "remote"
    OXIGRAPH = "oxigraph"
    RDFLIB = "rdflib"


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
    """The full, validated shape of a load/diff request."""

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
    except ValidationError as exc:
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
