# coding=utf-8
"""Running the skos-history diff of two dataset versions feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('../features/execute_skos_history.feature', 'Running the skos-history')
def _test_running_the_skoshistory():
    """Running the skos-history."""


@then('the DSV description is generated')
def the_dsv_description_is_generated():
    """the DSV description is generated."""
    raise NotImplementedError


@then('the dataset versions are loaded into the triplestore')
def the_dataset_versions_are_loaded_into_the_triplestore():
    """the dataset versions are loaded into the triplestore."""
    raise NotImplementedError


@then('the insertions and deletions graphs are created')
def the_insertions_and_deletions_graphs_are_created():
    """the insertions and deletions graphs are created."""
    raise NotImplementedError
