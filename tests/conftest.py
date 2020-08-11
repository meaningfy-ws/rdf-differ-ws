"""
conftest.py
Date: 11/08/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from collections import namedtuple

import pytest


class FakeSPARQLRunner:
    def __init__(self, result_format: str = 'json'):
        self.return_value = None

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
