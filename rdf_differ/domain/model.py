"""
model.py
Date: 11/08/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from dataclasses import dataclass


class VersionMissing(Exception):
    pass


class VersionExists(Exception):
    pass


class VersionDeltaExists(Exception):
    pass


class RDFContentReference:
    pass


class Dataset:
    def __init__(self, name: str, uri: str, description: str = ''):
        self.name = name
        self.uri = uri
        self.description = description
        self.versions = list()
        self.version_deltas = list()

    def add_version(self):
        pass

    def calculate_diff(self):
        pass


@dataclass
class DatasetVersion:
    version_id: str
    description: str
    content_reference: RDFContentReference


@dataclass
class VersionDeltas:
    old: str
    new: str
    insertions: RDFContentReference
    deletions: RDFContentReference
