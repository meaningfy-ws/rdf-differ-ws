"""
test_skos_history_wrapper.py
Date: 06/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from filecmp import cmp
from pathlib import Path

import pytest

from rdf_differ.skos_history_wrapper import SKOSHistoryRunner, SKOSHistoryFolderSetUp
from utils.file_utils import dir_exists


def helper_create_skos_runner(dataset='dataset', scheme_uri='http://scheme.uri', versions=None, basedir='/basedir',
                              filename='file.rdf', endpoint='http://test.point'):
    if versions is None:
        versions = ['v1', 'v2']
    return SKOSHistoryRunner(dataset, scheme_uri, versions, basedir, filename, endpoint)


test_values = [('test.rdf', 'application/rdf+xml'),
               ('test.rdfs', 'application/rdf+xml'),
               ('test.owl', 'application/rdf+xml'),
               ('test.n3', 'text/n3'),
               ('test.ttl', 'text/turtle'),
               ('test.json', 'application/json')]


@pytest.mark.parametrize("filename,file_format", test_values)
def test_input_file_mime_supported(filename, file_format):
    skos_runner = helper_create_skos_runner(filename=filename)
    assert skos_runner.input_file_mime == file_format


def test_input_file_mime_not_supported():
    skos_runner = helper_create_skos_runner(filename='test.doc')
    with pytest.raises(Exception) as exception:
        _ = skos_runner.input_file_mime

    assert 'File type not supported.' in str(exception.value)


def test_uris_creation():
    skos_runner = helper_create_skos_runner(dataset='dataset', endpoint='http://test.point')

    assert skos_runner.put_uri == 'http://test.point/dataset/data'
    assert skos_runner.update_uri == 'http://test.point/dataset'
    assert skos_runner.query_uri == 'http://test.point/dataset/query'


def test_generate_config(tmpdir):
    basedir = tmpdir.mkdir('basedir')
    skos_runner = helper_create_skos_runner(filename='file.rdf', basedir=basedir, endpoint='http://test.point')

    config_file = skos_runner.generate()
    expected_config_content = '''# !/bin/bash

DATASET = dataset
SCHEMEURI = http://scheme.uri

VERSIONS = (v1 v2)
BASEDIR = {basedir}
FILENAME = file.rdf

PUT_URI = http://test.point/dataset/data
UPDATE_URI = http://test.point/dataset
QUERY_URI = http://test.point/dataset/query

INPUT_MIME_TYPE = application/rdf+xml'''.format(basedir=basedir)
    expected_config = tmpdir.join('expected.config')
    expected_config.write(expected_config_content)

    assert cmp(config_file, expected_config)


def helper_create_skos_folder_setup(dataset='dataset', filename='file.rdf', alpha_file='alpha.rdf',
                                    beta_file='beta.rdf', root_path='root_path'):
    return SKOSHistoryFolderSetUp(dataset, filename, alpha_file, beta_file, root_path)


def test_skos_history_folder_setup_root_path_exist_is_not_empty(tmpdir):
    root_path = tmpdir.mkdir('root_path')
    file = root_path.join('file')
    file.write('')
    with pytest.raises(Exception) as exception:
        _ = helper_create_skos_folder_setup(root_path=str(root_path))

    assert 'Root path is not empty' in str(exception.value)


def test_skos_history_folder_setup_generate(tmpdir):
    dataset = 'dataset'
    filename = 'file.rdf'
    root_path = tmpdir.mkdir('root_path')
    alpha_file = tmpdir.join('alpha_file')
    alpha_file.write('alpha')
    beta_file = tmpdir.join('beta_file')
    beta_file.write('beta')

    skos_folder_setup = helper_create_skos_folder_setup(dataset=dataset, filename=filename, alpha_file=alpha_file,
                                                        beta_file=beta_file,
                                                        root_path=root_path)
    skos_folder_setup.generate()
    data_path = Path(root_path) / 'dataset/data'
    v1 = data_path / 'v1'
    v2 = data_path / 'v2'

    assert dir_exists(v1)
    assert dir_exists(v2)

    assert cmp(alpha_file, v1 / 'file.rdf')
    assert cmp(beta_file, v2 / 'file.rdf')
