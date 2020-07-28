# coding=utf-8
"""Prepare the skos-history config file and folder structure feature tests."""
from filecmp import cmp
from pathlib import Path

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

from tests.unit.conftest import helper_create_skos_runner
from utils.file_utils import dir_exists, dir_is_empty, file_exists


@scenario('../features/prepare_config.feature', 'Set up the folder structure')
def test_set_up_the_folder_structure():
    """Set up the folder structure."""


@scenario('../features/prepare_config.feature', 'Generating the skos-history config file')
def test_generating_the_skos_history_config_file():
    """Generating the skos-history config file."""


@given('mandatory descriptive metadata', target_fixture='metadata')
def mandatory_descriptive_metadata():
    """mandatory descriptive metadata."""
    metadata = {
        'basedir': 'basedir',
        'filename': 'file',
        'endpoint': 'http://test.point',
        'dataset': 'dataset',
        'scheme_uri': 'http://scheme.uri',
    }

    return metadata


@given('the root path of folder structure')
def the_root_path_of_folder_structure(tmpdir, metadata):
    """the root path of folder structure."""
    basedir = tmpdir.mkdir('basedir')

    metadata['basedir'] = basedir


@given('old version and new version RDF files')
def old_version_and_new_version_rdf_files(tmpdir, metadata):
    """old version and new version RDF files."""
    old_version = tmpdir.join('old_version.rdf')
    old_version.write('old_version')
    new_version = tmpdir.join('new_version.rdf')
    new_version.write('new_version')

    metadata['old_version_file'] = old_version
    metadata['old_version_id'] = 'v1'
    metadata['new_version_file'] = new_version
    metadata['new_version_id'] = 'v2'


@when('the user runs the folder structure generator')
def the_user_runs_the_folder_structure_generator(metadata):
    """the user runs the folder structure generator."""
    skos_folder_setup = helper_create_skos_runner(dataset=metadata.get('dataset'),
                                                  filename=metadata.get('filename'),
                                                  old_version_file=metadata.get('old_version_file'),
                                                  new_version_file=metadata.get('new_version_file'),
                                                  basedir=metadata.get('basedir'),
                                                  old_version_id=metadata.get('old_version_id'),
                                                  new_version_id=metadata.get('new_version_id'),
                                                  endpoint=metadata.get('endpoint'),
                                                  scheme_uri=metadata.get('scheme_uri'))
    skos_folder_setup.generate_structure()


@then('a correct dataset folder structure is created')
def data_path(metadata):
    """a correct dataset folder structure is created."""
    data_path = Path(metadata.get('basedir')) / 'dataset/data'
    assert dir_exists(data_path)


@then('a sub-folder is created for each dataset version')
def a_sub_folder_is_created_for_each_dataset_version(metadata):
    """a sub-folder is created for each dataset version."""
    data_path = Path(metadata.get('basedir')) / 'dataset/data'

    v1 = data_path / 'v1'
    v2 = data_path / 'v2'

    assert dir_exists(v1)
    assert dir_exists(v2)


@then('a dataset file is copied into the version sub-folder')
def a_dataset_file_is_copied_into_the_version_sub_folder(metadata):
    """a dataset file is copied into the version sub-folder."""
    metadata['v1'] = Path(metadata.get('basedir')) / 'dataset/data' / 'v1'
    metadata['v2'] = Path(metadata.get('basedir')) / 'dataset/data' / 'v2'

    assert not dir_is_empty(metadata.get('v1'))
    assert not dir_is_empty(metadata.get('v2'))


@then('the file is renamed to a standard file name')
def the_file_is_renamed_to_a_standard_file_name(metadata):
    """the file is renamed to a standard file name."""
    assert cmp(metadata.get('old_version_file'), metadata.get('v1') / 'file.rdf')
    assert cmp(metadata.get('new_version_file'), metadata.get('v2') / 'file.rdf')


@when('the user runs the config generator')
def the_user_runs_the_config_generator(metadata):
    """the user runs the config generator."""
    skos_runner = helper_create_skos_runner(dataset=metadata.get('dataset'),
                                            filename=metadata.get('filename'),
                                            old_version_file=metadata.get('old_version_file'),
                                            new_version_file=metadata.get('new_version_file'),
                                            basedir=metadata.get('basedir'),
                                            old_version_id=metadata.get('old_version_id'),
                                            new_version_id=metadata.get('new_version_id'),
                                            endpoint=metadata.get('endpoint'),
                                            scheme_uri=metadata.get('scheme_uri'))
    metadata['config_location'] = skos_runner.generate_config()


@then('a correct configuration file is created in the folder structure')
def a_correct_configuration_file_is_created_in_the_folder_structure(tmpdir, metadata):
    """a correct configuration file is created in the folder structure."""
    expected_config_content = '''#!/bin/bash

DATASET = dataset
SCHEMEURI = http://scheme.uri

VERSIONS = (v1 v2)
BASEDIR = {basedir}
FILENAME = file.rdf

PUT_URI = http://test.point/dataset/data
UPDATE_URI = http://test.point/dataset
QUERY_URI = http://test.point/dataset/query

INPUT_MIME_TYPE = application/rdf+xml'''.format(basedir=metadata.get('basedir'))
    expected_config = tmpdir.join('expected.config')
    expected_config.write(expected_config_content)

    assert file_exists(Path(metadata.get('basedir') / 'dataset.config'))
    assert cmp(metadata.get('config_location'), expected_config)
