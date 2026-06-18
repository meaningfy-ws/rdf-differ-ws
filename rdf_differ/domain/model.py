"""Core domain model (pydantic v2 — DEC-3, migrated from dataclasses).

Pure domain: pydantic is allowed here; no I/O frameworks. `DatasetVersion` and
`VersionsDelta` keep identity-based equality (by id / id-pair) so they behave as
value objects keyed on their identifiers, not their payloads.
"""

from pydantic import BaseModel, ConfigDict, Field


class VersionMissing(Exception):
    pass


class VersionExists(Exception):
    pass


class VersionsDeltaExists(Exception):
    pass


class RDFContentReference:
    """Marker for a reference to RDF content (version data / a delta component)."""


class DatasetVersion(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    version_id: str
    description: str | None = None
    content_reference: RDFContentReference | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DatasetVersion):
            return NotImplemented
        return self.version_id == other.version_id

    __hash__ = None  # type: ignore[assignment]  # identity by id; not hashable


class VersionsDelta(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    old_version_id: str
    new_version_id: str
    insertions: RDFContentReference | None = None
    deletions: RDFContentReference | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionsDelta):
            return NotImplemented
        return (
            self.old_version_id == other.old_version_id
            and self.new_version_id == other.new_version_id
        )

    __hash__ = None  # type: ignore[assignment]


class Dataset(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    uri: str
    description: str | None = ""
    versions: list[DatasetVersion] = Field(default_factory=list)
    version_deltas: list[VersionsDelta] = Field(default_factory=list)

    def add_version(self, dataset_version: DatasetVersion) -> None:
        if self._version_exists(dataset_version.version_id):
            raise VersionExists(
                f"This dataset version ({dataset_version.version_id}) already exists."
            )
        self.versions.append(dataset_version)

    def _version_exists(self, version_id: str) -> bool:
        return version_id in [known.version_id for known in self.versions]

    def get_delta(self, old_version_id: str, new_version_id: str) -> VersionsDelta | None:
        target = VersionsDelta(old_version_id=old_version_id, new_version_id=new_version_id)
        return next(filter(lambda existing: target == existing, self.version_deltas), None)

    def calculate_diff(self, old_version_id: str, new_version_id: str) -> VersionsDelta:
        if not (self._version_exists(old_version_id) and self._version_exists(new_version_id)):
            raise VersionMissing(
                f"In order to calculate a diff both versions ({old_version_id} and "
                f"{new_version_id}) must exist."
            )
        delta = self.get_delta(old_version_id=old_version_id, new_version_id=new_version_id)
        if not delta:
            delta = VersionsDelta(old_version_id=old_version_id, new_version_id=new_version_id)
            self.version_deltas.append(delta)
        return delta
