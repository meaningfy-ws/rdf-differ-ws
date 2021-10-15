#!/usr/bin/python3

# conftest.py
# Date: 11/08/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

from collections import namedtuple
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter
from rdf_differ.adapters.skos_history_wrapper import SKOSHistoryRunner
from rdf_differ.entrypoints.ui import app as ui_app


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


class FakeRedisClient:
    def __init__(self, lrange_return: list = None):
        self.actions = list()
        self.lrange_return = lrange_return

    def lpush(self, key, value):
        self.actions.append(('LEFT PUSH', key, value))

    def lrem(self, key, count, value):
        self.actions.append(('REMOVE VALUE FROM KEY', key, count, value))
        return 1

    def lrange(self, key, start, end):
        self.actions.append(('GET LIST FROM KEY', key, start, end))
        return self.lrange_return


@pytest.fixture(scope='function')
def fake_requests():
    return FakeRequests()


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
                          http_client=FakeRequests(),
                          sparql_client=FakeSPARQLRunner()):
    return FusekiDiffAdapter(triplestore_service_url=triplestore_service_url,
                             http_client=http_client,
                             sparql_client=sparql_client)


# TODO: update configuration handling https://flask.palletsprojects.com/en/1.1.x/config/#development-production
@pytest.fixture
def ui_client():
    ui_app.config['TESTING'] = True
    ui_app.config['WTF_CSRF_ENABLED'] = False

    return ui_app.test_client()


def helper_create_diff(file_1=None, file_2=None, body=None):
    file_1 = file_1 if file_1 else FileStorage((BytesIO(b'1')), filename='old_file.rdf')
    file_2 = file_2 if file_2 else FileStorage((BytesIO(b'2')), filename='new_file.rdf')
    body = body if body else {
        'dataset_id': 'dataset',
        'dataset_uri': 'uri',
        'old_version_id': 'old',
        'new_version_id': 'new',
    }
    return file_1, file_2, body
