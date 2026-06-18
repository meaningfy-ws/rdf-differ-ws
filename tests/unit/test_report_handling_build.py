from unittest.mock import patch

import pytest
from werkzeug.exceptions import UnprocessableEntity

from rdf_differ.services.report_handling import build_report

DATASET = {
    "query_url": "http://query",
    "original_name": "original",
    "old_version_file": "old.rdf",
    "new_version_file": "new.rdf",
}


@patch("rdf_differ.services.report_handling.ReportBuilder")
@patch("rdf_differ.services.report_handling.shutil.copytree")
def test_build_report_returns_output_path(mock_copytree, mock_builder, tmp_path):
    (tmp_path / "config.json").write_text('{"template": "main.html"}', encoding="utf-8")

    result = build_report(str(tmp_path), "template_loc", {}, "ap", "ds", DATASET, "ts")

    assert str(result).endswith("output/main.html")
    mock_builder.return_value.make_document.assert_called_once()


@patch("rdf_differ.services.report_handling.ReportBuilder")
@patch("rdf_differ.services.report_handling.shutil.copytree")
def test_build_report_missing_config_raises(mock_copytree, mock_builder, tmp_path):
    # no config.json copied into temp_dir
    with pytest.raises(UnprocessableEntity):
        build_report(str(tmp_path), "template_loc", {}, "ap", "ds", DATASET, "ts")
