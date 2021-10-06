#!/usr/bin/python3

# test_tasks.py
# Date: 06/10/2021
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from unittest.mock import patch

import pytest

from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.services.tasks import async_create_diff
from utils.file_utils import dir_is_empty, dir_exists


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
