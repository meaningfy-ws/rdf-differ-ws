import pytest

from rdf_differ.diffing.domain.exceptions import VersionMissing
from rdf_differ.diffing.domain.model import (
    Dataset,
    DatasetVersion,
    RDFContentReference,
    VersionsDelta,
)


def test_dataset_version_equality_is_by_version_id():
    assert DatasetVersion(version_id="v1", description="desc") == DatasetVersion(
        version_id="v1", description="other", content_reference=RDFContentReference()
    )
    assert DatasetVersion(version_id="v1") != DatasetVersion(version_id="v2")


def test_dataset_version_not_equal_to_other_types():
    assert DatasetVersion(version_id="v1") != "v1"


def test_versions_delta_equality_is_by_version_pair():
    assert VersionsDelta(old_version_id="old", new_version_id="new") == VersionsDelta(
        old_version_id="old",
        new_version_id="new",
        insertions=RDFContentReference(),
        deletions=RDFContentReference(),
    )
    assert VersionsDelta(old_version_id="old", new_version_id="new") != VersionsDelta(
        old_version_id="old", new_version_id="other"
    )


def test_versions_delta_not_equal_to_other_types():
    assert VersionsDelta(old_version_id="old", new_version_id="new") != 42


def test_new_dataset_has_no_versions_or_deltas():
    dataset = Dataset(name="ds", uri="http://ds")
    assert dataset.name == "ds"
    assert dataset.uri == "http://ds"
    assert dataset.versions == []
    assert dataset.version_deltas == []


def test_add_version_appends_a_version():
    dataset = Dataset(name="ds", uri="http://ds")
    dataset.add_version(DatasetVersion(version_id="v1"))
    assert dataset.versions == [DatasetVersion(version_id="v1")]


def test_add_duplicate_version_raises():
    dataset = Dataset(name="ds", uri="http://ds")
    dataset.add_version(DatasetVersion(version_id="v1"))
    with pytest.raises(Exception, match="v1.*already exists"):
        dataset.add_version(DatasetVersion(version_id="v1"))


def test_calculate_diff_with_missing_version_raises():
    dataset = Dataset(name="ds", uri="http://ds")
    dataset.add_version(DatasetVersion(version_id="v1"))
    with pytest.raises(VersionMissing):
        dataset.calculate_diff("v1", "v2")


def test_calculate_diff_creates_and_caches_a_delta():
    dataset = Dataset(name="ds", uri="http://ds")
    dataset.add_version(DatasetVersion(version_id="v1"))
    dataset.add_version(DatasetVersion(version_id="v2"))

    delta = dataset.calculate_diff("v1", "v2")

    assert delta == VersionsDelta(old_version_id="v1", new_version_id="v2")
    assert dataset.version_deltas == [delta]
    again = dataset.calculate_diff("v1", "v2")
    assert again == delta
    assert len(dataset.version_deltas) == 1


def test_get_delta_returns_none_when_absent():
    dataset = Dataset(name="ds", uri="http://ds")
    assert dataset.get_delta("v1", "v2") is None
