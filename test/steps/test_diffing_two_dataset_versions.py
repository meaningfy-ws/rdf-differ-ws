# coding=utf-8
"""Diffing two dataset versions feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('../features/diffing_two_dataset_versions.feature', 'Controlling the mandatory descriptive metadata')
def _test_controlling_the_mandatory_descriptive_metadata():
    """Controlling the mandatory descriptive metadata."""


@scenario('../features/diffing_two_dataset_versions.feature', 'Diffing two dataset versions')
def _test_diffing_two_dataset_versions():
    """Diffing two dataset versions."""


@given('alpha and beta RDF files')
def alpha_and_beta_rdf_files():
    """alpha and beta RDF files."""
    raise NotImplementedError


@given('mandatory descriptive metadata')
def mandatory_descriptive_metadata():
    """mandatory descriptive metadata."""
    raise NotImplementedError


@given('the <property> is missing or incorrect')
def the_property_is_missing_or_incorrect():
    """the <property> is missing or incorrect."""
    raise NotImplementedError


@when('the user runs the diff calculator')
def the_user_runs_the_diff_calculator():
    """the user runs the diff calculator."""
    raise NotImplementedError


@then('a correct configuration file is created')
def a_correct_configuration_file_is_created():
    """a correct configuration file is created."""
    raise NotImplementedError


@then('a correct dataset folder structure is created')
def a_correct_dataset_folder_structure_is_created():
    """a correct dataset folder structure is created."""
    raise NotImplementedError


@then('an error message is generated indicating the <property> problem')
def an_error_message_is_generated_indicating_the_property_problem():
    """an error message is generated indicating the <property> problem."""
    raise NotImplementedError


@then('the diff calculator is executed')
def the_diff_calculator_is_executed():
    """the diff calculator is executed."""
    raise NotImplementedError


@then('the files are copied and renamed accordingly in the folder structure')
def the_files_are_copied_and_renamed_accordingly_in_the_folder_structure():
    """the files are copied and renamed accordingly in the folder structure."""
    raise NotImplementedError

