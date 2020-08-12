"""
conftest.py
Date: 11/08/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from collections import namedtuple

import pytest

from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter
from rdf_differ.adapters.skos_history_wrapper import SKOSHistoryRunner


class FakeSPARQLRunner:
    def __init__(self, result_format: str = 'json'):
        self.return_value = {
            'head': {'vars': []},
            'results': {'bindings': []}
        }

    def execute(self, endpoint_url: str, query_text: str):
        return self.return_value


@pytest.fixture(scope='function')
def fake_sparql_runner():
    return FakeSPARQLRunner('http://some.url')


RequestObj = namedtuple('RequestObj', ['status_code', 'url', 'text'])


class FakeRequests:

    def __init__(self):
        self.text = None
        self.status_code = None
        self.url = None

    def get(self, url, params=None, **kwargs):
        self.url = url
        return self

    def delete(self, url, **kwargs):
        self.url = url
        return self

    def post(self, url, data=None, json=None, **kwargs):
        self.url = url
        return self


@pytest.fixture(scope='function')
def fake_requests():
    return FakeRequests()


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
