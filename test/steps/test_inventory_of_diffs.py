# coding=utf-8
"""List the diffs in the triplestore feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('../features/inventory_of_diffs.feature', 'Query the triplestore')
def _test_query_the_triplestore():
    """Query the triplestore."""


@given('a set of well defined SPARQL queries for inventory checking')
def a_set_of_well_defined_sparql_queries_for_inventory_checking():
    """a set of well defined SPARQL queries for inventory checking."""
    raise NotImplementedError


@given('an output folder is provided')
def an_output_folder_is_provided():
    """an output folder is provided."""
    raise NotImplementedError


@given('the configured endpoint')
def the_configured_endpoint():
    """the configured endpoint."""
    raise NotImplementedError


@when('the user requests the diff inventory')
def the_user_requests_the_diff_inventory():
    """the user requests the diff inventory."""
    raise NotImplementedError


@then('the datasetURI is returned')
def the_dataseturi_is_returned():
    """the datasetURI is returned."""
    raise NotImplementedError


@then('at least two dataset versions are returned')
def at_least_two_dataset_versions_are_returned():
    """at least two dataset versions are returned."""
    raise NotImplementedError


@then('the count of deleted and inserted triples are returned')
def the_count_of_deleted_and_inserted_triples_are_returned():
    """the count of deleted and inserted triples are returned."""
    raise NotImplementedError

