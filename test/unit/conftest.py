"""
conftest.py
Date: 20/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from rdf_differ.skos_history_wrapper import SKOSHistoryRunner


def helper_endpoint_mock(monkeypatch):
    monkeypatch.setenv('ENDPOINT', 'http://test.point')


def helper_create_skos_runner(dataset='dataset', scheme_uri='http://scheme.uri', endpoint='http://test.point',
                              basedir='/basedir', old_version_file='old.rdf', new_version_file='new.rdf',
                              old_version_id='v1', new_version_id='v2', filename='file'):
    return SKOSHistoryRunner(dataset=dataset,
                             scheme_uri=scheme_uri,
                             basedir=basedir,
                             filename=filename,
                             endpoint=endpoint,
                             old_version_file=old_version_file,
                             new_version_file=new_version_file,
                             old_version_id=old_version_id,
                             new_version_id=new_version_id)
