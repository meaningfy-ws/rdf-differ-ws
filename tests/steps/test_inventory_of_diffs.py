#!/usr/bin/python3

# test_inventory_of_diffs.py
# Date:  07/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

"""List the diffs in the triplestore feature tests."""
import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

from tests import DUMMY_DATASET_DIFF_DESCRIPTION, DUMMY_DATASET_DELETED_COUNT, DUMMY_DATASET_INSERTED_COUNT
from tests.conftest import helper_fuseki_service


@pytest.fixture()
def fuseki_diff_getter():
    """create fuseki fixture"""
    return helper_fuseki_service()


@pytest.fixture()
def diff_object():
    """create diff_object fixture"""
    return list()


@scenario('../features/inventory_of_diffs.feature', 'Query the triplestore')
def test_query_the_triplestore():
    """Query the triplestore."""


@given('a set of well defined SPARQL queries for inventory checking')
def a_set_of_well_defined_spqrql_queries_for_inventory_checking():
    pass


@given('the configured endpoint')
def the_configured_endpoint():
    pass


@when('the user requests the diff inventory')
def the_user_requests_the_diff_inventory(fake_sparql_runner, fuseki_diff_getter, diff_object):
    """the user requests the diff inventory."""
    dataset = '/subdiv'
    fake_sparql_runner.return_value = DUMMY_DATASET_DIFF_DESCRIPTION
    fuseki_diff_getter.sparql_client = fake_sparql_runner
    diff_object.append(fuseki_diff_getter.dataset_description(dataset))

    fake_sparql_runner.return_value = DUMMY_DATASET_INSERTED_COUNT
    fuseki_diff_getter.sparql_client = fake_sparql_runner
    diff_object.append(fuseki_diff_getter.count_inserted_triples(dataset))

    fake_sparql_runner.return_value = DUMMY_DATASET_DELETED_COUNT
    fuseki_diff_getter.sparql_client = fake_sparql_runner
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
