#!/usr/bin/python3

# test_tasks.py
# Date: 06/10/2021
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from unittest.mock import patch

import pytest

from rdf_differ.adapters.celery import async_create_diff, async_generate_report
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.config import RDF_DIFFER_REPORTS_DB
from rdf_differ.utils.file_utils import dir_exists


@patch.object(FusekiDiffAdapter, 'create_diff')
@patch.object(FusekiDiffAdapter, 'inject_metadata')
def test_async_create_diff_success(mock_inject_metadata, mock_create_diff, tmpdir):
    cleanup_location = tmpdir.mkdir('files-location')
    new_version_file = cleanup_location.join('new_version.rdf')
    old_version_file = cleanup_location.join('old_version.rdf')

    return_value = async_create_diff('dataset', {}, old_version_file, new_version_file, cleanup_location, RDF_DIFFER_REPORTS_DB)

    mock_create_diff.assert_called_once()
    mock_inject_metadata.assert_called_once()

    assert not dir_exists(cleanup_location)
    assert True == return_value


@patch.object(FusekiDiffAdapter, 'create_diff')
@patch.object(FusekiDiffAdapter, 'inject_metadata')
def test_async_create_diff_failure(mock_inject_metadata, mock_create_diff, tmpdir):
    mock_create_diff.side_effect = FusekiException()

    cleanup_location = tmpdir.mkdir('files-location')
    new_version_file = cleanup_location.join('new_version.rdf')
    old_version_file = cleanup_location.join('old_version.rdf')

    with pytest.raises(FusekiException) as e:
        async_create_diff('dataset', {}, old_version_file, new_version_file, cleanup_location, RDF_DIFFER_REPORTS_DB)

    assert not dir_exists(cleanup_location)


@patch('rdf_differ.adapters.celery.save_report')
@patch('rdf_differ.adapters.celery.build_report')
def test_async_create_report_success(mock_build_report, mock_save_report, tmpdir):
    db = tmpdir.mkdir('db')
    template_location = tmpdir.mkdir('template_location')
    dataset_id = 'dataset'
    dataset_name = 'dataset_name'
    application_profile = 'ap'
    template_type = 'tp'
    return_value = async_generate_report(dataset_id, application_profile, template_type, db, template_location, {},
                                         {'uid': dataset_id, 'dataset_name': dataset_name})

    mock_build_report.assert_called_once()
    mock_save_report.assert_called_once()

    assert return_value
