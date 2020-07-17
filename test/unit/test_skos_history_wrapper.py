"""
test_skos_history_wrapper.py
Date: 06/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from filecmp import cmp
from pathlib import Path
from unittest.mock import patch

import pytest

from rdf_differ import defaults
from rdf_differ.skos_history_wrapper import SKOSHistoryRunner, SKOSHistoryFolderSetUp
from rdf_differ.utils import dir_exists


def helper_endpoint_mock(monkeypatch):
    monkeypatch.setenv('ENDPOINT', 'http://test.point')


def helper_create_skos_runner(dataset='dataset', scheme_uri='http://scheme.uri', versions=None):
    if versions is None:
        versions = ['v1', 'v2']
    return SKOSHistoryRunner(dataset, scheme_uri, versions)


@pytest.fixture
def mock_env_basedir(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.setenv('BASEDIR', '/basedir')


def test_read_envs_basedir_exists(mock_env_basedir):
    skos_runner = helper_create_skos_runner()
    assert skos_runner.basedir == '/basedir'


@pytest.fixture
def mock_env_basedir_missing(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.delenv("BASEDIR", raising=False)


def test_read_envs_basedir_doesnt_exist(mock_env_basedir_missing):
    skos_runner = helper_create_skos_runner()
    assert skos_runner.basedir == defaults.BASEDIR


@pytest.fixture
def mock_env_filename(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.setenv('FILENAME', 'test.rdf')


def test_read_envs_filename_exists(mock_env_filename):
    skos_runner = helper_create_skos_runner()
    assert skos_runner.filename == 'test.rdf'


@pytest.fixture
def mock_env_filename_missing(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.delenv("FILENAME", raising=False)


def test_read_envs_filename_doesnt_exist(mock_env_filename_missing):
    skos_runner = helper_create_skos_runner()
    assert skos_runner.filename == defaults.FILENAME


@pytest.fixture
def mock_env_endpoint(monkeypatch):
    helper_endpoint_mock(monkeypatch)


def test_read_envs_endpoint_exists(mock_env_endpoint):
    skos_runner = helper_create_skos_runner()
    assert skos_runner.endpoint == 'http://test.point'


@pytest.fixture
def mock_env_endpoint_missing(monkeypatch):
    monkeypatch.delenv("ENDPOINT", raising=False)


def test_read_envs_endpoint_doesnt_exist(mock_env_endpoint_missing):
    with pytest.raises(KeyError) as key_error:
        skos_runner = helper_create_skos_runner()

    assert 'ENDPOINT' in str(key_error.value)


test_values = [['test.rdf', 'application/rdf+xml'],
               ['test.rdfs', 'application/rdf+xml'],
               ['test.owl', 'application/rdf+xml'],
               ['test.n3', 'text/n3'],
               ['test.ttl', 'text/turtle'],
               ['test.json', 'application/json']]


@pytest.fixture(params=test_values)
def mock_file_type_success(monkeypatch, request):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.setenv('FILENAME', request.param[0])
    return request.param[1]


@pytest.mark.parametrize("mock_file_type_success", test_values, indirect=True)
def test_input_file_mime_supported(mock_file_type_success):
    skos_runner = helper_create_skos_runner()
    assert skos_runner.input_file_mime == mock_file_type_success


@pytest.fixture
def mock_file_type_failure(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.setenv('FILENAME', 'test.doc')


def test_input_file_mime_not_supported(mock_file_type_failure):
    skos_runner = helper_create_skos_runner()
    with pytest.raises(Exception) as exception:
        _ = skos_runner.input_file_mime

    assert 'File type not supported.' in str(exception.value)


def test_uris_creation(mock_env_endpoint):
    skos_runner = helper_create_skos_runner(dataset='dataset')

    assert skos_runner.put_uri == 'http://test.point/dataset/data'
    assert skos_runner.update_uri == 'http://test.point/dataset'
    assert skos_runner.query_uri == 'http://test.point/dataset/query'


@pytest.fixture
def mock_all_envs(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.setenv('BASEDIR', '/basedir')
    monkeypatch.setenv('FILENAME', 'test.rdf')


def test_generate_config(mock_all_envs):
    skos_runner = helper_create_skos_runner()

    config = skos_runner.generate()
    expected_config = '''# !/bin/bash

DATASET = dataset
SCHEMEURI = http://scheme.uri

VERSIONS = (v1 v2)
BASEDIR = /basedir
FILENAME = test.rdf

PUT_URI = http://test.point/dataset/data
UPDATE_URI = http://test.point/dataset
QUERY_URI = http://test.point/dataset/query

INPUT_MIME_TYPE = application/rdf+xml'''
    assert config == expected_config


def helper_create_skos_folder_setup(dataset='dataset', alpha_file='alpha.rdf',
                                    beta_file='beta.rdf', root_path='root_path'):
    return SKOSHistoryFolderSetUp(dataset, alpha_file, beta_file, root_path)


@patch.object(Path, 'mkdir')
def test_skos_history_folder_setup_root_path_doest_exist(mock_mkdir):
    root_path = Path.cwd().joinpath('root_folder')
    _ = helper_create_skos_folder_setup(root_path=str(root_path))

    mock_mkdir.assert_called_once()


@patch.object(Path, 'mkdir')
def test_skos_history_folder_setup_root_path_exist_is_empty(mock_mkdir, tmpdir):
    root_path = tmpdir.mkdir('root_path')
    _ = helper_create_skos_folder_setup(root_path=str(root_path))

    mock_mkdir.assert_not_called()


def test_skos_history_folder_setup_root_path_exist_is_not_empty(tmpdir):
    root_path = tmpdir.mkdir('root_path')
    file = root_path.join('file')
    file.write('')
    with pytest.raises(Exception) as exception:
        _ = helper_create_skos_folder_setup(root_path=str(root_path))

    assert 'Root path is not empty' in str(exception.value)


def test_skos_history_folder_setup_generate(tmpdir):
    root_path = tmpdir.mkdir('root_path')
    alpha_file = tmpdir.join('alpha_file')
    alpha_file.write('alpha')
    beta_file = tmpdir.join('beta_file')
    beta_file.write('beta')
    dataset = 'dataset'

    skos_folder_setup = helper_create_skos_folder_setup(dataset=dataset, alpha_file=alpha_file, beta_file=beta_file,
                                                        root_path=root_path)
    skos_folder_setup.generate()
    data_path = Path(root_path) / 'dataset/data'
    v1 = data_path / 'v1'
    v2 = data_path / 'v2'

    assert dir_exists(v1)
    assert dir_exists(v2)

    assert cmp(alpha_file, v1 / 'file.rdf')
    assert cmp(beta_file, v2 / 'file.rdf')
