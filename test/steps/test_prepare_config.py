# coding=utf-8
"""Prepare the skos-history config file and folder structure feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('../features/prepare_config.feature', 'Generating the skos-history config file')
def _test_generating_the_skos_history_config_file():
    """Generating the skos-history config file."""


@scenario('../features/prepare_config.feature', 'Set up the folder structure')
def _test_set_up_the_folder_structure():
    """Set up the folder structure."""


@given('alpha and beta RDF files')
def alpha_and_beta_rdf_files():
    """alpha and beta RDF files."""
    raise NotImplementedError


@given('mandatory descriptive metadata')
def mandatory_descriptive_metadata():
    """mandatory descriptive metadata."""
    raise NotImplementedError


@given('the root path of folder structure')
def the_root_path_of_folder_structure():
    """the root path of folder structure."""
    raise NotImplementedError


@when('the user runs the config generator')
def the_user_runs_the_config_generator():
    """the user runs the config generator."""
    raise NotImplementedError


@when('the user runs the folder structure generator')
def the_user_runs_the_folder_structure_generator():
    """the user runs the folder structure generator."""
    raise NotImplementedError


@then('a correct configuration file is created in the folder structure')
def a_correct_configuration_file_is_created_in_the_folder_structure():
    """a correct configuration file is created in the folder structure."""
    raise NotImplementedError


@then('a correct dataset folder structure is created')
def a_correct_dataset_folder_structure_is_created():
    """a correct dataset folder structure is created."""
    raise NotImplementedError


@then('a dataset file is copied into the version sub-folder')
def a_dataset_file_is_copied_into_the_version_subfolder():
    """a dataset file is copied into the version sub-folder."""
    raise NotImplementedError


@then('a sub-folder is created for each dataset version')
def a_subfolder_is_created_for_each_dataset_version():
    """a sub-folder is created for each dataset version."""
    raise NotImplementedError


@then('the file is renamed to a standard file name')
def the_file_is_renamed_to_a_standard_file_name():
    """the file is renamed to a standard file name."""
    raise NotImplementedError

