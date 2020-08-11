"""
conftest.py
Date: 20/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from rdf_differ.diff_adapter import FusekiDiffAdapter
from rdf_differ.skos_history_wrapper import SKOSHistoryRunner
from tests.conftest import FakeRequests, FakeSPARQLRunner


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


def helper_fuseki_service(triplestore_service_url: str = "http://localhost:3030/",
                          http_requests=FakeRequests(),
                          sparql_requests=FakeSPARQLRunner()):
    return FusekiDiffAdapter(triplestore_service_url=triplestore_service_url,
                             http_requests=http_requests,
                             sparql_requests=sparql_requests)
