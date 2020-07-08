# coding=utf-8
"""List the diffs in the triplestore feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('../features/inventory_of_diffs.feature', 'Query the triplestore')
def test_query_the_triplestore():
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


@then('the non-empty query result-sets are writen into output files')
def the_nonempty_query_resultsets_are_writen_into_output_files():
    """the non-empty query result-sets are writen into output files."""
    raise NotImplementedError


@then('the result-set file is named based on the query file with a timestamp suffix')
def the_resultset_file_is_named_based_on_the_query_file_with_a_timestamp_suffix():
    """the result-set file is named based on the query file with a timestamp suffix."""
    raise NotImplementedError


@then('the the inventory queries are executed on the endpoint')
def the_the_inventory_queries_are_executed_on_the_endpoint():
    """the the inventory queries are executed on the endpoint."""
    raise NotImplementedError

