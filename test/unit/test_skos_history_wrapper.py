"""
test_skos_history_wrapper.py
Date: 06/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""

import pytest

from rdf_differ.skos_history_wrapper import SKOSHistoryRunner


def helper_create_skos_runner(dataset='dataset', scheme_uri='http://scheme.uri', basedir='/basedir',
                              filename='file.rdf', endpoint='http://test.point', old_version_file='old.rdf',
                              new_version_file='new.rdf', old_version_id='v1', new_version_id='v2'):

    return SKOSHistoryRunner(dataset=dataset,
                             filename=filename,
                             old_version_file=old_version_file,
                             new_version_file=new_version_file,
                             basedir=basedir,
                             old_version_id=old_version_id,
                             new_version_id=new_version_id,
                             endpoint=endpoint,
                             scheme_uri=scheme_uri)


test_values = [('test.rdf', 'application/rdf+xml'),
               ('test.trix', 'application/xml'),
               ('test.nq', 'application/n-quads'),
               ('test.nt', 'application/n-triples'),
               ('test.ttl', 'text/turtle'),
               ('test.n3', 'text/n3'),
               ('test.jsonld', 'application/ld+json')]


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


def test_skos_history_folder_setup_root_path_exist_is_not_empty(tmpdir):
    root_path = tmpdir.mkdir('root_path')
    file = root_path.join('file')
    file.write('')
    with pytest.raises(Exception) as exception:
        _ = helper_create_skos_runner(basedir=str(root_path))

    assert 'Root path is not empty' in str(exception.value)
