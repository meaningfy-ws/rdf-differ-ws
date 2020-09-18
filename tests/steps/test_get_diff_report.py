# coding=utf-8
"""Get RDF Diff HTML report feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('../features/get_diff_report.feature', 'Successfully generate a RDF diff report')
def _test_successfully_generate_a_rdf_diff_report():
    """Successfully generate a RDF diff report."""


@scenario('../features/get_diff_report.feature', 'Dataset requested doesn\'t exist')
def _test_dataset_requested_doesnt_exist():
    """Dataset requested doesn't exist."""


@given('the dataset id and endpoint')
def the_dataset_id_and_endpoint(scenario_context):
    """the dataset id and endpoint."""
    scenario_context['dataset_id'] = 'dataset'
    scenario_context['dataset_url'] = 'some url'


@when('API endpoint is called')
def api_endpoint_is_called():
    """API endpoint is called."""
    raise NotImplementedError


@then('it contains the RDF diff information')
def it_contains_the_rdf_diff_information():
    """it contains the RDF diff information."""
    raise NotImplementedError


@then('the HTML file is generated')
def the_html_file_is_generated():
    """the HTML file is generated."""
    raise NotImplementedError


@when('API endpoint is called with missing dataset')
def api_endpoint_is_called_with_missing_dataset():
    """API endpoint is called."""
    raise NotImplementedError


@then('the user is notified that the dataset doesn\'t exist')
def the_user_is_notified_that_the_dataset_doesnt_exist():
    """the user is notified that the dataset doesn't exist."""
    raise NotImplementedError

