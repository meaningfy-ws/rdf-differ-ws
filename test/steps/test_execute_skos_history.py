# coding=utf-8
"""Running the skos-history diff of two dataset versions feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('../features/execute_skos_history.feature', 'Controlling the skos-history inputs')
def _test_controlling_the_skoshistory_inputs():
    """Controlling the skos-history inputs."""


@scenario('../features/execute_skos_history.feature', 'Running the skos-history')
def _test_running_the_skoshistory():
    """Running the skos-history."""


@given('a <configuration file>')
def a_configuration_file():
    """a <configuration file>."""
    raise NotImplementedError


@given('a <folder structure>')
def a_folder_structure():
    """a <folder structure>."""
    raise NotImplementedError


@given('a correct configuration file')
def a_correct_configuration_file():
    """a correct configuration file."""
    raise NotImplementedError


@given('a correct dataset folder structure')
def a_correct_dataset_folder_structure():
    """a correct dataset folder structure."""
    raise NotImplementedError


@when('the user runs the skos-history calculator')
def the_user_runs_the_skoshistory_calculator():
    """the user runs the skos-history calculator."""
    raise NotImplementedError


@then('an error message is generated indicating the <problem>')
def an_error_message_is_generated_indicating_the_problem():
    """an error message is generated indicating the <problem>."""
    raise NotImplementedError


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

