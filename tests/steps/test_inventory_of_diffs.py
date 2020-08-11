# coding=utf-8
"""List the diffs in the triplestore feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

from rdf_differ.diff_adapter import FusekiDiffAdapter


@scenario('../features/inventory_of_diffs.feature', 'Query the triplestore')
def test_query_the_triplestore():
    """Query the triplestore."""


@given('a set of well defined SPARQL queries for inventory checking')
def fuseki_diff_getter():
    """create fuseki fixture"""
    return FusekiDiffAdapter("http://localhost:3030")


@given('the configured endpoint')
def diff_object():
    """create diff_object fixture"""
    return list()


@when('the user requests the diff inventory')
def the_user_requests_the_diff_inventory(fuseki_diff_getter, diff_object):
    """the user requests the diff inventory."""
    dataset = '/subdiv'
    diff_object.append(fuseki_diff_getter.diff_description(dataset))
    diff_object.append(fuseki_diff_getter.count_inserted_triples(dataset))
    diff_object.append(fuseki_diff_getter.count_deleted_triples(dataset))


@then('the datasetURI is returned')
def the_dataset_uri_is_returned(diff_object):
    """the datasetURI is returned."""
    assert diff_object[0]['dataset_uri'] == 'http://publications.europa.eu/resource/authority/subdivision'


@then('at least two dataset versions are returned')
def at_least_two_dataset_versions_are_returned(diff_object):
    """at least two dataset versions are returned."""
    assert len(diff_object[0]['dataset_versions']) == 2


@then('the count of deleted and inserted triples are returned')
def the_count_of_deleted_and_inserted_triples_are_returned(diff_object):
    """the count of deleted and inserted triples are returned.
    the data is taken from tests/test_data/subdivisions_sh_ds/data
    """
    assert diff_object[1] == 387
    assert diff_object[2] == 3
