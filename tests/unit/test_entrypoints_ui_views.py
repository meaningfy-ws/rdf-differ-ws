#!/usr/bin/python3

# test_entrypoints_ui_views.py
# Date:  18/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from io import BytesIO
from unittest.mock import patch

from bs4 import BeautifulSoup
from werkzeug.datastructures import FileStorage


@patch('rdf_differ.entrypoints.ui.views.get_datasets')
def test_index(mock_get_datasets, ui_client):
    mock_get_datasets.return_value = [
                                         {
                                             'dataset_id': '/dataset_one',
                                         },
                                         {
                                             'dataset_id': '/dataset_two',
                                         },
                                     ], 200

    response = ui_client.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')

    title = soup.find('h1')
    assert 'List of calculated diffs' in title.get_text()

    table_body = soup.find('tbody')
    rows = table_body.find_all('tr')
    assert 2 == len(rows)
    assert '/dataset_one' in rows[0].get_text()
    assert '/dataset_two' in rows[1].get_text()


@patch('rdf_differ.entrypoints.ui.views.get_dataset')
def test_get_dataset(mock_get_dataset, ui_client):
    dataset_id = 'dataset_one'
    mock_get_dataset.return_value = {
                                        'dataset_id': f'/{dataset_id}',
                                        'dataset_uri': 'http://dataset.one',
                                        'new_version_id': 'one_new',
                                        'old_version_id': 'one_old',
                                        'dataset_versions': ['one_new', 'one_old'],
                                        'version_named_graphs': ['http://one.version/one_old',
                                                                 'http://one.version/one_new'],
                                        'diff_date': '2020'
                                    }, 200

    response = ui_client.get(f'/diffs/{dataset_id}')
    soup = BeautifulSoup(response.data, 'html.parser')

    title = soup.find('h1')
    assert 'You\'re viewing dataset: /dataset_one' in title.get_text()

    table_body = soup.find('tbody')
    rows = table_body.find_all('tr')
    assert 7 == len(rows)
    assert 'http://dataset.one' in rows[1].get_text()
    assert 'one_new' in rows[2].get_text()
    assert 'one_old' in rows[2].get_text()
    assert 'http://one.version/one_old' in rows[4].get_text()
    assert 'http://one.version/one_new' in rows[4].get_text()
    assert 'one_new' in rows[5].get_text()
    assert 'one_old' in rows[6].get_text()


@patch('rdf_differ.entrypoints.ui.views.get_dataset')
@patch('rdf_differ.entrypoints.ui.views.api_create_diff')
def test_create_diff_success(mock_create_diff, mock_get_dataset, ui_client):
    mock_create_diff.return_value = {}, 200
    # required data for the redirect after successful submission
    mock_get_dataset.return_value = {
                                        'dataset_id': '/dataset_name',
                                        'dataset_uri': 'http://dataset.uri',
                                        'new_version_id': 'new_version_id',
                                        'old_version_id': 'old_version_id',
                                        'dataset_versions': ['old_version_id', 'new_version_id'],
                                        'version_named_graphs': ['http://one.version/one_old',
                                                                 'http://one.version/one_new'],
                                        'diff_date': '2020'
                                    }, 200

    response = ui_client.get('/create-diff')
    soup = BeautifulSoup(response.data, 'html.parser')

    title = soup.find('h1')
    assert 'Create a dataset' in title.get_text()

    data = {
        'dataset_name': 'dataset_name',
        'dataset_description': 'dataset description',
        'dataset_uri': 'http://dataset.uri',
        'old_version_file_content': FileStorage(BytesIO(b'old content'), 'old.rdf'),
        'new_version_file_content': FileStorage(BytesIO(b'new content'), 'new.rdf'),
        'old_version_id': 'old_version_id',
        'new_version_id': 'new_version_id'
    }

    response = ui_client.post('/create-diff', data=data, follow_redirects=True,
                              content_type='multipart/form-data')

    soup = BeautifulSoup(response.data, 'html.parser')
    title = soup.find('h1')

    assert response.status_code == 200
    assert 'You\'re viewing dataset: /dataset_name' in title.get_text()


@patch('rdf_differ.entrypoints.ui.views.api_create_diff')
def test_create_diff_incorrect_dataset_name(mock_create_diff, ui_client):
    mock_create_diff.return_value = {}, 200

    data = {
        'dataset_name': 'dataset name',
        'dataset_description': 'dataset description',
        'dataset_uri': 'http://dataset.uri',
        'old_version_file_content': FileStorage(BytesIO(b'old content'), 'old.rdf'),
        'new_version_file_content': FileStorage(BytesIO(b'new content'), 'new.rdf'),
        'old_version_id': 'old_version_id',
        'new_version_id': 'new_version_id'
    }

    response = ui_client.post('/create-diff', data=data, follow_redirects=True,
                              content_type='multipart/form-data')

    soup = BeautifulSoup(response.data, 'html.parser')
    body = soup.get_text()

    assert 'Dataset name can contain only letters, numbers, _, :, and -' in body

    data['dataset_name'] = '&3fldsaj//'
    data['old_version_file_content'] = FileStorage(BytesIO(b'old content'), 'old.rdf')
    data['new_version_file_content'] = FileStorage(BytesIO(b'new content'), 'new.rdf')

    response = ui_client.post('/create-diff', data=data, follow_redirects=True,
                              content_type='multipart/form-data')

    soup = BeautifulSoup(response.data, 'html.parser')
    body = soup.get_text()

    assert 'Dataset name can contain only letters, numbers, _, :, and -' in body


@patch('rdf_differ.entrypoints.ui.views.get_report')
def test_download_report_success(mock_get_report, ui_client):
    dataset_id = 'dataset'
    mock_get_report.return_value = b'important report', 200

    response = ui_client.get(f'/diff-report/{dataset_id}')
    assert 'important report' in response.data.decode()


@patch('rdf_differ.entrypoints.ui.views.get_datasets')
@patch('rdf_differ.entrypoints.ui.views.get_report')
def test_download_report_failure(mock_get_report, mock_get_datasets, ui_client):
    dataset_id = 'dataset'
    mock_get_report.side_effect = Exception('report error')
    mock_get_datasets.return_value = [], 200

    response = ui_client.get(f'/diff-report/{dataset_id}')
    soup = BeautifulSoup(response.data, 'html.parser')

    # check if redirected to index page
    title = soup.find('h1')
    assert 'List of calculated diffs' in title.get_text()

    # check if error is displayed
    error = soup.find('div', {'class': 'alert alert-danger'})
    assert 'report error' in error.get_text()
