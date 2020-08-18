"""
model.py
Date: 11/08/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from dataclasses import dataclass
from typing import Optional


class VersionMissing(Exception):
    pass


class VersionExists(Exception):
    pass


class VersionsDeltaExists(Exception):
    pass


class RDFContentReference:
    pass


@dataclass
class DatasetVersion:
    version_id: str
    description: Optional[str]
    content_reference: Optional[RDFContentReference]

    def __eq__(self, other: 'DatasetVersion'):
        return self.version_id == other.version_id


@dataclass
class VersionsDelta:
    old_version_id: str
    new_version_id: str
    insertions: Optional[RDFContentReference]
    deletions: Optional[RDFContentReference]

    def __eq__(self, other: 'VersionsDelta'):
        return self.old_version_id == other.old_version_id and self.new_version_id == other.new_version_id


class Dataset:
    def __init__(self, name: str, uri: str, description: Optional[str] = ''):
        self.name = name
        self.uri = uri
        self.description = description
        self.versions = list()
        self.version_deltas = list()

    def add_version(self, dataset_version: DatasetVersion):
        if self._version_exists(dataset_version.version_id):
            raise VersionExists(f"This dataset version ({dataset_version.version_id}) already exists.")
        self.versions.append(dataset_version)

    def _version_exists(self, dataset_version: str) -> bool:
        if dataset_version in [known_version.version_id for known_version in self.versions]:
            return True
        return False

    def get_delta(self, old_version_id: str, new_version_id: str) -> Optional[VersionsDelta]:
        target_delta = VersionsDelta(old_version_id=old_version_id, new_version_id=new_version_id, insertions=None,
                                     deletions=None)
        return next(filter(lambda existent_delta: target_delta == existent_delta,
                           self.version_deltas), None)

    def calculate_diff(self, old_version_id: str, new_version_id: str) -> VersionsDelta:
        if not (self._version_exists(old_version_id) and self._version_exists(new_version_id)):
            raise VersionMissing(
                f"In order to calculate a diff both versions ({old_version_id} and {new_version_id}) must exist.")

        delta = self.get_delta(old_version_id=old_version_id, new_version_id=new_version_id)
        if not delta:
            # TODO: provide a insertions/deletion abstract fetcher
            delta = VersionsDelta(old_version_id=old_version_id, new_version_id=new_version_id, deletions=None,
                                  insertions=None)
            self.version_deltas.append(delta)
        return delta
