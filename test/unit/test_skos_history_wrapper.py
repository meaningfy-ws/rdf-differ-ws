"""
test_skos_history_wrapper.py
Date: 06/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from pathlib import Path
from unittest.mock import patch

import pytest

from rdf_differ.skos_history_wrapper import SKOSHistoryRunner
from test.unit.conftest import helper_create_skos_runner


@pytest.mark.parametrize("filename, file_format", [('test.rdf', 'application/rdf+xml'),
                                                   ('test.trix', 'application/xml'),
                                                   ('test.nq', 'application/n-quads'),
                                                   ('test.nt', 'application/n-triples'),
                                                   ('test.ttl', 'text/turtle'),
                                                   ('test.n3', 'text/n3'),
                                                   ('test.jsonld', 'application/ld+json')])
def test_input_file_mime_supported(filename, file_format):
    skos_runner = helper_create_skos_runner(filename=filename)

    assert skos_runner.get_file_format(filename) == file_format


def test_input_file_mime_not_supported():
    filename = 'test.doc'
    skos_runner = helper_create_skos_runner()
    with pytest.raises(Exception) as exception:
        _ = skos_runner.get_file_format(filename)

    assert 'Format of "test.doc" is not supported.' in str(exception.value)


def test_file_formats_equal():
    skos_runner = helper_create_skos_runner(old_version_file='old.rdf', new_version_file='new.rdf')

    assert skos_runner.file_format == 'application/rdf+xml'


def test_file_formats_different():
    with pytest.raises(Exception) as exception:
        _ = helper_create_skos_runner(old_version_file='old.rdf', new_version_file='new.trix')

    assert 'File formats are different: application/rdf+xml, application/xml' in str(exception.value)


def test_uris_creation():
    skos_runner = helper_create_skos_runner(dataset='dataset', endpoint='http://test.point')

    assert skos_runner.put_uri == 'http://test.point/dataset/data'
    assert skos_runner.update_uri == 'http://test.point/dataset'
    assert skos_runner.query_uri == 'http://test.point/dataset/query'


def test_skos_history_folder_setup_root_path_exist_is_not_empty(tmpdir):
    root_path = tmpdir.mkdir('root_path')
    file = root_path.join('file')
    file.write('')
    with pytest.raises(Exception) as exception:
        _ = helper_create_skos_runner(basedir=str(root_path))

    assert 'Root path is not empty' in str(exception.value)


def test_skos_history_execute_subprocess(tmpdir):
    skos_runner = helper_create_skos_runner()
    # get absolute path as script is wonky when relative path is used
    test_data_location = Path(__file__).parent.parent / 'test_data/subdivisions_sh_ds/data'
    config_content = f"""#!/bin/bash
DATASET=ds-subdivision
SCHEMEURI="http://publications.europa.eu/resource/authority/subdivision"

VERSIONS=(v1 v2)
BASEDIR={test_data_location}
FILENAME=subdivisions-skos.rdf

PUT_URI=http://localhost:3030/subdiv/data
UPDATE_URI=http://localhost:3030/subdiv
QUERY_URI=http://localhost:3030/subdiv/query

INPUT_MIME_TYPE="application/rdf+xml"
"""
    config_file = tmpdir.join('test.config')
    config_file.write(config_content)

    output = skos_runner.execute_subprocess(config_file)

    assert 'Initializing the version history graph with the current version' in output
    assert 'Loading version http://publications.europa.eu/resource/authority/subdivision/version/v1' in output
    assert 'Loading version http://publications.europa.eu/resource/authority/subdivision/version/v2' in output
    assert 'Creating the delta http://publications.europa.eu/resource/authority/subdivision/version/v1/delta/v2' in output


@patch.object(SKOSHistoryRunner, 'execute_subprocess')
@patch.object(SKOSHistoryRunner, 'generate_config')
@patch.object(SKOSHistoryRunner, 'generate_structure')
def test_skos_history_run(mock_generate_structure, mock_generate_config, mock_execute_subprocess):
    skos_runner = helper_create_skos_runner()
    skos_runner.run()
    mock_generate_structure.asssert_called_once()
    mock_generate_config.asssert_called_once()
    mock_execute_subprocess.asssert_called_once()
