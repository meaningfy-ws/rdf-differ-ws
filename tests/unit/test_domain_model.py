import pytest

from rdf_differ.domain.model import (
    Dataset,
    DatasetVersion,
    RDFContentReference,
    VersionMissing,
    VersionsDelta,
)


def test_dataset_version_equality_is_by_version_id():
    assert DatasetVersion("v1", "desc", None) == DatasetVersion(
        "v1", "other", RDFContentReference()
    )
    assert DatasetVersion("v1", None, None) != DatasetVersion("v2", None, None)


def test_dataset_version_not_equal_to_other_types():
    assert DatasetVersion("v1", None, None) != "v1"


def test_versions_delta_equality_is_by_version_pair():
    assert VersionsDelta("old", "new", None, None) == VersionsDelta(
        "old", "new", RDFContentReference(), RDFContentReference()
    )
    assert VersionsDelta("old", "new", None, None) != VersionsDelta("old", "other", None, None)


def test_versions_delta_not_equal_to_other_types():
    assert VersionsDelta("old", "new", None, None) != 42


def test_new_dataset_has_no_versions_or_deltas():
    dataset = Dataset(name="ds", uri="http://ds")
    assert dataset.name == "ds"
    assert dataset.uri == "http://ds"
    assert dataset.versions == []
    assert dataset.version_deltas == []


def test_add_version_appends_a_version():
    dataset = Dataset("ds", "http://ds")
    dataset.add_version(DatasetVersion("v1", None, None))
    assert dataset.versions == [DatasetVersion("v1", None, None)]


def test_add_duplicate_version_raises():
    dataset = Dataset("ds", "http://ds")
    dataset.add_version(DatasetVersion("v1", None, None))
    with pytest.raises(Exception, match="v1.*already exists"):
        dataset.add_version(DatasetVersion("v1", None, None))


def test_calculate_diff_with_missing_version_raises():
    dataset = Dataset("ds", "http://ds")
    dataset.add_version(DatasetVersion("v1", None, None))
    with pytest.raises(VersionMissing):
        dataset.calculate_diff("v1", "v2")


def test_calculate_diff_creates_and_caches_a_delta():
    dataset = Dataset("ds", "http://ds")
    dataset.add_version(DatasetVersion("v1", None, None))
    dataset.add_version(DatasetVersion("v2", None, None))

    delta = dataset.calculate_diff("v1", "v2")

    assert delta == VersionsDelta("v1", "v2", None, None)
    assert dataset.version_deltas == [delta]
    # a second call returns the cached delta (no duplicate appended)
    again = dataset.calculate_diff("v1", "v2")
    assert again == delta
    assert len(dataset.version_deltas) == 1


def test_get_delta_returns_none_when_absent():
    dataset = Dataset("ds", "http://ds")
    assert dataset.get_delta("v1", "v2") is None
