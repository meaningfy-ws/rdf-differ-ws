import json

import pytest
from pydantic import ValidationError

from rdf_differ import config
from rdf_differ.core.adapters.filesystem import read_meta_file
from rdf_differ.reporting.domain.model import ReportMeta
from rdf_differ.reporting.services.report_handling import (
    find_dataset_name_by_id,
    generate_meta_file,
    get_all_reports,
    retrieve_report,
)


def _write_meta(folder, uid, dataset_name):
    """Write a meta file with the configured name into ``folder``."""
    folder.mkdir(parents=True, exist_ok=True)
    payload = {"uid": uid, "dataset_name": dataset_name}
    (folder / config.RDF_DIFFER_META_NAME).write_text(json.dumps(payload))


# --- find_dataset_name_by_id ------------------------------------------------


def test_find_dataset_name_by_id_returns_name_among_multiple_folders(tmp_path):
    """The dataset_name is returned for the folder whose meta uid matches."""
    _write_meta(tmp_path / "ds1", "uid-1", "ds1")
    _write_meta(tmp_path / "ds2", "uid-2", "ds2")

    assert find_dataset_name_by_id("uid-2", str(tmp_path)) == "ds2"


def test_find_dataset_name_by_id_skips_folder_without_meta(tmp_path):
    """A folder lacking a meta file is skipped and the search still finds the match."""
    (tmp_path / "stray").mkdir()
    _write_meta(tmp_path / "ds2", "uid-2", "ds2")

    assert find_dataset_name_by_id("uid-2", str(tmp_path)) == "ds2"


def test_find_dataset_name_by_id_returns_empty_when_no_match(tmp_path):
    """An empty string is returned when no folder's meta uid matches."""
    _write_meta(tmp_path / "ds1", "uid-1", "ds1")

    assert find_dataset_name_by_id("missing", str(tmp_path)) == ""


# --- retrieve_report --------------------------------------------------------


def test_retrieve_report_returns_empty_when_dir_missing(tmp_path):
    """Missing report directory yields an empty string instead of raising."""
    assert retrieve_report("ds", "ap", "variant", str(tmp_path)) == ""


def test_retrieve_report_returns_empty_when_dir_empty(tmp_path):
    """An existing but empty report directory yields an empty string."""
    (tmp_path / "ds" / "ap" / "variant").mkdir(parents=True)

    assert retrieve_report("ds", "ap", "variant", str(tmp_path)) == ""


def test_retrieve_report_returns_file_path_when_report_present(tmp_path):
    """The path of the report file is returned when one exists."""
    report_dir = tmp_path / "ds" / "ap" / "variant"
    report_dir.mkdir(parents=True)
    report_file = report_dir / "report.html"
    report_file.write_text("content")

    assert retrieve_report("ds", "ap", "variant", str(tmp_path)) == str(report_file)


# --- get_all_reports --------------------------------------------------------


def test_get_all_reports_lists_application_profiles_and_variations(tmp_path):
    """Each application profile is listed with its template variations."""
    (tmp_path / "ds" / "ap1" / "variant-a").mkdir(parents=True)
    (tmp_path / "ds" / "ap1" / "variant-b").mkdir(parents=True)
    (tmp_path / "ds" / "ap2" / "variant-c").mkdir(parents=True)

    reports = get_all_reports("ds", str(tmp_path))

    by_profile = {entry["application_profile"]: entry for entry in reports}
    assert set(by_profile) == {"ap1", "ap2"}
    assert sorted(by_profile["ap1"]["template_variations"]) == ["variant-a", "variant-b"]
    assert by_profile["ap2"]["template_variations"] == ["variant-c"]


def test_get_all_reports_returns_empty_when_no_reports_dir(tmp_path):
    """An empty list is returned for a dataset that has no reports directory."""
    assert get_all_reports("nonexistent", str(tmp_path)) == []


# --- ReportMeta domain model ------------------------------------------------


def test_report_meta_uid_defaults_to_none_and_round_trips(tmp_path):
    """uid defaults to None and the meta survives a generate/read round-trip."""
    meta = ReportMeta(dataset_name="ds", created_at="ts")
    assert meta.model_dump()["uid"] is None

    written = generate_meta_file(str(tmp_path), None, "ds", "ts")
    assert read_meta_file(tmp_path) == written


def test_report_meta_missing_dataset_name_raises(tmp_path):
    """A missing dataset_name is rejected by the model."""
    with pytest.raises(ValidationError):
        ReportMeta(created_at="ts")


# --- generate_meta_file timestamp default -----------------------------------


def test_generate_meta_file_empty_timestamp_writes_created_at(tmp_path):
    """An empty timestamp is replaced by a generated, non-empty created_at."""
    meta_data = generate_meta_file(str(tmp_path), "uid-1", "ds", "")

    assert meta_data["created_at"]
