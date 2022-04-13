#!/usr/bin/python3

# external.py
# Date: 11/08/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

from SPARQLWrapper import SPARQLWrapper, JSON, POST, BASIC


class SPARQLRunner:
    """
    Wrapper around the SPARQLWrapper python package.
    Used for Dependency Injection.
    """

    def __init__(self, result_format: str = JSON):
        self.result_format = result_format

    def execute(self, endpoint_url: str, query_text: str):
        runner = SPARQLWrapper(endpoint_url)
        runner.setQuery(query_text)
        runner.setReturnFormat(self.result_format)
        return runner.query().convert()

    def execute_update(self, endpoint_url: str, query_text: str, login: str = None, password: str = None):
        runner = SPARQLWrapper(endpoint_url)
        runner.setHTTPAuth(BASIC)
        runner.setCredentials(login, password)
        runner.setMethod(POST)
        runner.setQuery(query_text)
        results = runner.query()
        return results.response.read()
