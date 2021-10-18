#!/usr/bin/python3

# test_tasks.py
# Date: 06/10/2021
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from unittest.mock import patch

import pytest

from rdf_differ.adapters.celery import async_create_diff, async_generate_report
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter, FusekiException
from utils.file_utils import dir_exists


@patch.object(FusekiDiffAdapter, 'create_diff')
def test_async_create_diff_success(mock_create_diff, tmpdir):
    cleanup_location = tmpdir.mkdir('files-location')
    new_version_file = cleanup_location.join('new_version.rdf')
    old_version_file = cleanup_location.join('old_version.rdf')

    return_value = async_create_diff({}, old_version_file, new_version_file, cleanup_location)

    mock_create_diff.assert_called_once()

    assert not dir_exists(cleanup_location)
    assert True == return_value


@patch.object(FusekiDiffAdapter, 'create_diff')
def test_async_create_diff_failure(mock_create_diff, tmpdir):
    mock_create_diff.side_effect = FusekiException()

    cleanup_location = tmpdir.mkdir('files-location')
    new_version_file = cleanup_location.join('new_version.rdf')
    old_version_file = cleanup_location.join('old_version.rdf')

    with pytest.raises(FusekiException) as e:
        async_create_diff({}, old_version_file, new_version_file, cleanup_location)

    assert not dir_exists(cleanup_location)


@patch('rdf_differ.adapters.celery.save_report')
@patch('rdf_differ.adapters.celery.build_report')
def test_async_create_report_success(mock_build_report, mock_save_report, tmpdir):
    db = tmpdir.mkdir('db')
    template_location = tmpdir.mkdir('template_location')
    dataset_id = 'dataset'
    application_profile = 'ap'
    template_type = 'tp'
    return_value = async_generate_report(template_location, {}, {'dataset_id': dataset_id}, application_profile,
                                         template_type, db)

    mock_build_report.assert_called_once()
    mock_save_report.assert_called_once()

    assert True == return_value