#!/usr/bin/python3

# test_entrypoints_diffs.py
# Date: 07/08/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

from unittest.mock import patch

import pytest
from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from werkzeug.exceptions import InternalServerError, Conflict, BadRequest, NotFound

from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.adapters.skos_history_wrapper import SKOSHistoryRunner, SubprocessFailure
from rdf_differ.entrypoints.api.handlers import get_diffs, create_diff, get_diff, delete_diff
from tests.unit.conftest import helper_create_diff


@patch.object(FusekiDiffAdapter, 'dataset_description')
@patch.object(FusekiDiffAdapter, 'list_datasets')
def test_get_diffs_200(mock_list_datasets, mock_dataset_description):
    mock_list_datasets.return_value = ['first_dataset', 'second_dataset']
    mock_dataset_description.side_effect = [
        ({
            'dataset_id': "first_dataset"
        }),
        ({
            'dataset_id': "second_dataset"
        })
    ]

    response, status = get_diffs()

    assert status == 200
    assert response == [
        {
            'dataset_id': "first_dataset"
        },
        {
            'dataset_id': "second_dataset"
        }
    ]


@patch.object(FusekiDiffAdapter, 'list_datasets')
def test_get_diffs_500(mock_list_datasets):
    mock_list_datasets.side_effect = FusekiException('500 exception')

    with pytest.raises(InternalServerError) as e:
        _ = get_diffs()

    assert '500 exception' in str(e.value)


@patch.object(FusekiDiffAdapter, 'dataset_description')
@patch.object(SKOSHistoryRunner, '__init__')
@patch.object(SKOSHistoryRunner, 'run')
def test_create_diff_200_empty_dataset(_, mock_init, mock_dataset_description):
    mock_init.return_value = None
    mock_dataset_description.return_value = {}

    file_1, file_2, body = helper_create_diff()

    response, status = create_diff(body=body,
                                   old_version_file_content=file_1,
                                   new_version_file_content=file_2)

    assert "Request to create a new dataset diff successfully accepted for processing." in response
    assert status == 200


@patch.object(FusekiDiffAdapter, 'create_dataset')
@patch.object(FusekiDiffAdapter, 'dataset_description')
@patch.object(SKOSHistoryRunner, '__init__')
@patch.object(SKOSHistoryRunner, 'run')
def test_create_diff_200_dataset_doesnt_exist(_, mock_init, mock_dataset_description, mock_create_dataset):
    mock_init.return_value = None
    mock_dataset_description.side_effect = EndPointNotFound

    file_1, file_2, body = helper_create_diff()

    response, status = create_diff(body=body,
                                   old_version_file_content=file_1,
                                   new_version_file_content=file_2)

    mock_create_dataset.assert_called_once()
    assert "Request to create a new dataset diff successfully accepted for processing." in response
    assert status == 200


@patch.object(SKOSHistoryRunner, '__init__')
@patch.object(SKOSHistoryRunner, 'run')
def test_create_diff_400(_, mock_init):
    mock_init.side_effect = ValueError('Value error')

    file_1, file_2, body = helper_create_diff()

    with pytest.raises(BadRequest) as e:
        _ = create_diff(body=body,
                        old_version_file_content=file_1,
                        new_version_file_content=file_2)

    assert 'Value error' in str(e.value)


@patch.object(FusekiDiffAdapter, 'dataset_description')
def test_create_diff_409(mock_dataset_description):
    mock_dataset_description.return_value = {'dataset_uri': 'http://some.uri'}

    file_1, file_2, body = helper_create_diff()

    with pytest.raises(Conflict) as e:
        _ = create_diff(body=body,
                        old_version_file_content=file_1,
                        new_version_file_content=file_2)


@patch.object(SKOSHistoryRunner, '__init__')
@patch.object(SKOSHistoryRunner, 'run')
def test_create_diff_500(_, mock_init):
    mock_init.side_effect = SubprocessFailure()

    file_1, file_2, body = helper_create_diff()

    with pytest.raises(InternalServerError) as e:
        _ = create_diff(body=body,
                        old_version_file_content=file_1,
                        new_version_file_content=file_2)

    assert 'Internal error while uploading the diffs.' in str(e.value)


@patch.object(FusekiDiffAdapter, 'dataset_description')
def test_get_diff_200(mock_dataset_description):
    mock_dataset_description.return_value = {'dataset_id': "dataset"}

    response, status = get_diff('dataset')

    assert status == 200
    assert response == {'dataset_id': "dataset"}


@patch.object(FusekiDiffAdapter, 'dataset_description')
def test_get_diff_404(mock_dataset_description):
    mock_dataset_description.side_effect = EndPointNotFound

    with pytest.raises(NotFound) as e:
        _ = get_diff('dataset')

    assert "<dataset> does not exist." in str(e.value)


@pytest.mark.parametrize('exception', [ValueError, IndexError])
@patch.object(FusekiDiffAdapter, 'dataset_description')
def test_get_diff_500(mock_dataset_description, exception):
    mock_dataset_description.side_effect = exception

    with pytest.raises(InternalServerError) as e:
        _ = get_diff('dataset')

    assert "Unexpected Error." in str(e.value)


# TODO: update tests after refactoring. Add 5xx testing
@patch.object(FusekiDiffAdapter, 'delete_dataset')
def test_delete_diff_200(mock_delete_dataset):
    mock_delete_dataset.return_value = "", 200

    response, status = delete_diff('dataset')

    assert '<dataset> created successfully.' in response
    assert status == 200


@patch.object(FusekiDiffAdapter, 'delete_dataset')
def test_delete_diff_404(mock_delete_dataset):
    mock_delete_dataset.side_effect = FusekiException

    with pytest.raises(NotFound) as e:
        _ = delete_diff('dataset')

    assert "<dataset> does not exist." in str(e.value)
