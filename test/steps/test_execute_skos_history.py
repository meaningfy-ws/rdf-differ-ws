# coding=utf-8
"""
Generate the diff of two dataset versions feature tests.
Date:  07/07/2020
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com
"""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

import test


@scenario('../features/execute_skos_history.feature', 'Incorrect config scenario')
def test_incorrect_config_scenario():
    """Incorrect config scenario."""


@scenario('../features/execute_skos_history.feature', 'Incorrect folder structure scenario')
def test_incorrect_folder_structure_scenario():
    """Incorrect folder structure scenario."""


@scenario('../features/execute_skos_history.feature', 'Main success scenario')
def test_main_success_scenario():
    """Main success scenario."""


@given('a correct configuration file')
def a_correct_configuration_file():
    """a correct configuration file."""
    return test.SUBDIVISIONS_CONFIG


@given('a correct dataset folder structure')
def a_correct_dataset_folder_structure():
    """a correct dataset folder structure."""
    return test.SUBDIVISIONS_DATA_FOLDER


@given('an incorrect configuration file')
def an_incorrect_configuration_file():
    """an incorrect configuration file."""
    raise NotImplementedError


@given('an incorrect dataset folder structure')
def an_incorrect_dataset_folder_structure():
    """an incorrect dataset folder structure."""
    raise NotImplementedError


@when('the user runs the diff calculator')
def the_user_runs_the_diff_calculator():
    """the user runs the diff calculator."""
    raise NotImplementedError


@then('an error message is generated indicating the config problem')
def an_error_message_is_generated_indicating_the_config_problem():
    """an error message is generated indicating the config problem."""
    raise NotImplementedError


@then('an error message is generated indicating the folder structure problem')
def an_error_message_is_generated_indicating_the_folder_structure_problem():
    """an error message is generated indicating the folder structure problem."""
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
