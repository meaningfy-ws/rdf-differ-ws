"""
conftest.py
Date: 20/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""


def helper_endpoint_mock(monkeypatch):
    monkeypatch.setenv('ENDPOINT', 'http://test.point')
