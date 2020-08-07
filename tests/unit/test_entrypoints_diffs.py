"""
test_entrypoints_diffs.py
Date: 07/08/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from io import BytesIO
from unittest.mock import patch

from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from werkzeug.datastructures import FileStorage

from rdf_differ.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.entrypoints.diffs import get_diffs, create_diff, get_diff, delete_diff
from rdf_differ.skos_history_wrapper import SKOSHistoryRunner, SKOSException


@patch.object(FusekiDiffAdapter, 'diff_description')
@patch.object(FusekiDiffAdapter, 'list_datasets')
def test_get_diffs_200(mock_list_datasets, mock_diff_description):
    mock_list_datasets.return_value = (['first_dataset', 'second_dataset'], 200)
    mock_diff_description.side_effect = [
        ({
             'dataset_id': "first_dataset"
         }, None),
        ({
             'dataset_id': "second_dataset"
         }, None)
    ]

    response, status = get_diffs()

    assert status == 200
    assert response == [
        {'first_dataset': {
            'dataset_id': "first_dataset"
        }},
        {'second_dataset': {
            'dataset_id': "second_dataset"
        }}
    ]


@patch.object(FusekiDiffAdapter, 'list_datasets')
def test_get_diffs_500(mock_list_datasets):
    mock_list_datasets.side_effect = FusekiException('500 exception')

    response, status = get_diffs()

    assert response == '500 exception'
    assert status == 500


@patch.object(SKOSHistoryRunner, '__init__')
@patch.object(SKOSHistoryRunner, 'run')
def test_create_diff_202(_, mock_init):
    mock_init.return_value = None

    file_1 = FileStorage((BytesIO(b'1')), filename='old_file.rdf')
    file_2 = FileStorage((BytesIO(b'2')), filename='new_file.rdf')
    body = {
        'dataset_id': 'dataset',
        'dataset_uri': 'uri',
        'old_version_id': 'old',
        'new_version_id': 'new',
    }
    response, status = create_diff(body, file_1, file_2)

    assert "Request to create a new dataset diff successfully accepted for processing, " \
           "but the processing has not been completed." in response
    assert status == 202


@patch.object(SKOSHistoryRunner, '__init__')
@patch.object(SKOSHistoryRunner, 'run')
def test_creat_diff_500(_, mock_init):
    mock_init.side_effect = SKOSException('500 exception')

    file_1 = FileStorage((BytesIO(b'1')), filename='old_file.rdf')
    file_2 = FileStorage((BytesIO(b'2')), filename='new_file.rdf')
    body = {}
    response, status = create_diff(body, file_1, file_2)

    assert '500 exception' in response
    assert status == 500


@patch.object(FusekiDiffAdapter, 'diff_description')
def test_get_diff_200(mock_diff_description):
    mock_diff_description.return_value = {'dataset_id': "dataset"}, 200

    response, status = get_diff('dataset')

    assert status == 200
    assert response == {'dataset_id': "dataset"}


@patch.object(FusekiDiffAdapter, 'diff_description')
def test_get_diff_404(mock_diff_description):
    mock_diff_description.side_effect = EndPointNotFound()

    response, status = get_diff('dataset')

    assert status == 404
    assert response == "<dataset> does not exist."


@patch.object(FusekiDiffAdapter, 'diff_description')
def test_get_diff_500(mock_diff_description):
    mock_diff_description.side_effect = Exception()

    response, status = get_diff('dataset')

    assert status == 500
    assert response == "Unexpected Error."


# TODO: update tests after refactoring. Add 5xx testing
@patch.object(FusekiDiffAdapter, 'delete_dataset')
def test_delete_diff_200(mock_diff_description):
    mock_diff_description.return_value = "", 200

    response, status = delete_diff('dataset')

    assert status == 200
    assert response == ""


@patch.object(FusekiDiffAdapter, 'delete_dataset')
def test_delete_diff_404(mock_diff_description):
    mock_diff_description.return_value = "", 404

    response, status = delete_diff('dataset')

    assert status == 404
    assert response == ""
