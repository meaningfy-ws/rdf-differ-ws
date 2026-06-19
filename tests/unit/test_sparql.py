from unittest.mock import patch

from rdf_differ.core.adapters.sparql import SPARQLRunner


@patch("rdf_differ.core.adapters.sparql.SPARQLWrapper")
def test_execute_runs_query_and_converts(mock_wrapper):
    runner = mock_wrapper.return_value
    runner.query.return_value.convert.return_value = {"results": {}}

    result = SPARQLRunner().execute("http://endpoint", "SELECT * WHERE {}")

    assert result == {"results": {}}
    runner.setQuery.assert_called_once_with("SELECT * WHERE {}")


@patch("rdf_differ.core.adapters.sparql.SPARQLWrapper")
def test_execute_update_sets_credentials_and_returns_response(mock_wrapper):
    runner = mock_wrapper.return_value
    runner.query.return_value.response.read.return_value = b"OK"

    result = SPARQLRunner().execute_update("http://endpoint", "INSERT {}", login="u", password="p")

    assert result == b"OK"
    runner.setCredentials.assert_called_once_with("u", "p")
