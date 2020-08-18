"""
test_model.py
Date: 11/08/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from uuid import uuid4

import pytest

from rdf_differ.domain.model import Dataset, DatasetVersion, RDFContentReference, VersionExists, VersionsDeltaExists, \
    VersionMissing


@pytest.fixture()
def a_dataset(name: str = 'dataset', uri: str = 'http://some.uri', description: str = '') -> Dataset:
    return Dataset(name=name, uri=uri, description=description)


@pytest.fixture(scope="function")
def a_dataset_version(version_id: str = uuid4(), description: str = 'This si a dataset version',
                      content_reference: RDFContentReference = RDFContentReference()) -> DatasetVersion:
    return DatasetVersion(version_id=version_id, description=description, content_reference=content_reference)


@pytest.fixture(scope="module")
def a_dataset_with_v1_v2(name: str = 'dataset', uri: str = 'http://some.uri', description: str = ''):
    dataset = Dataset(name=name, uri=uri, description=description)
    dataset_version_1 = DatasetVersion(version_id="v1", description="", content_reference=None)
    dataset_version_2 = DatasetVersion(version_id="v2", description="", content_reference=None)

    dataset.add_version(dataset_version_1)
    dataset.add_version(dataset_version_2)

    return dataset


def test_dataset_add_version(a_dataset, a_dataset_version):
    a_dataset.add_version(a_dataset_version)

    assert len(a_dataset.versions) == 1


def test_dataset_add_version_already_exists(a_dataset, a_dataset_version):
    a_dataset.add_version(a_dataset_version)

    with pytest.raises(VersionExists):
        a_dataset.add_version(a_dataset_version)


def test_dataset_calculate_diff_already_exists(a_dataset_with_v1_v2):
    diff1 = a_dataset_with_v1_v2.calculate_diff(old_version_id='v1',
                                                new_version_id='v2')

    diff2 = a_dataset_with_v1_v2.calculate_diff(old_version_id='v1',
                                                new_version_id='v2')

    assert diff1 is diff2


def test_dataset_calculate_diff(a_dataset_with_v1_v2):
    diff = a_dataset_with_v1_v2.calculate_diff(old_version_id="v1",
                                               new_version_id="v2")

    assert diff.old_version_id == 'v1'
    assert diff.new_version_id == 'v2'
    assert len(a_dataset_with_v1_v2.version_deltas) == 1

    diff = a_dataset_with_v1_v2.calculate_diff(old_version_id="v1",
                                               new_version_id="v2")

    assert len(a_dataset_with_v1_v2.version_deltas) == 1


def test_dataset_calculate_diff_missing_dataset_version(a_dataset_with_v1_v2):
    with pytest.raises(VersionMissing):
        diff = a_dataset_with_v1_v2.calculate_diff(old_version_id='v1',
                                                   new_version_id='v3')
