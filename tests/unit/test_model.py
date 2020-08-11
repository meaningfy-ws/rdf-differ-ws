"""
test_model.py
Date: 11/08/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from uuid import uuid4

import pytest

from rdf_differ.domain.model import Dataset, DatasetVersion, RDFContentReference, VersionExists, VersionDeltaExists, \
    VersionMissing


def helper_dataset(name: str = 'dataset', uri: str = 'http://some.uri', description: str = '') -> Dataset:
    return Dataset(name=name, uri=uri, description=description)


def helper_dataset_version(version_id: str = uuid4(), description: str = '',
                           content_reference: RDFContentReference = RDFContentReference()) -> DatasetVersion:
    return DatasetVersion(version_id=version_id, description=description, content_reference=content_reference)


def test_dataset_add_version():
    dataset = helper_dataset()
    dataset_version = helper_dataset_version(version_id='v1')
    dataset.add_version(dataset_version)

    assert len(dataset.versions) == 1


def test_dataset_calculate_diff():
    dataset = helper_dataset()
    dataset_version_1 = helper_dataset_version(version_id='v1')
    dataset_version_2 = helper_dataset_version(version_id='v2')

    dataset.add_version(dataset_version_1)
    dataset.add_version(dataset_version_2)

    diff = dataset.calculate_diff(old=dataset_version_1.version_id,
                                  new=dataset_version_2.version_id)

    assert diff.old == 'v1'
    assert diff.new == 'v2'
    assert len(diff.version_deltas) == 1
    assert diff.insertions is not None
    assert diff.deletions is not None


def test_dataset_add_version_already_exists():
    dataset = helper_dataset()
    dataset_version_1 = helper_dataset_version(version_id='v1')
    dataset.add_version(dataset_version_1)

    with pytest.raises(VersionExists):
        dataset.add_version(dataset_version_1)


def test_dataset_calculate_diff_already_exists():
    dataset = helper_dataset()
    dataset_version_1 = helper_dataset_version(version_id='v1')
    dataset_version_2 = helper_dataset_version(version_id='v2')

    diff = dataset.calculate_diff(old=dataset_version_1.version_id,
                                  new=dataset_version_2.version_id)

    with pytest.raises(VersionDeltaExists):
        diff = dataset.calculate_diff(old=dataset_version_1.version_id,
                                      new=dataset_version_2.version_id)


def test_dataset_calculate_diff_missing_dataset_version():
    dataset = helper_dataset()
    dataset_version_2 = helper_dataset_version(version_id='v2')

    with pytest.raises(VersionMissing):
        diff = dataset.calculate_diff(old='v1',
                                      new=dataset_version_2.version_id)
