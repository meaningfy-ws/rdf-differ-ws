#!/usr/bin/python3

# test_diffing_two_dataset_versions.py
# Date:  08/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

"""Diffing two dataset versions feature tests."""

import shutil
from pathlib import Path

import pytest
import requests
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

from rdf_differ.adapters.skos_history_wrapper import SKOSHistoryRunner
from rdf_differ.adapters.sparql import SPARQLRunner
from rdf_differ.config import RDF_DIFFER_ENDPOINT_SERVICE
from tests.conftest import helper_fuseki_service
from utils.file_utils import dir_exists


@pytest.fixture()
def files(tmpdir):
    """alpha and beta RDF files."""
    old_version_file = tmpdir.join('old_version.rdf')
    shutil.copy(Path('tests/test_data/subdivisions_sh_ds/data/v1/subdivisions-skos.rdf'), old_version_file)
    new_version_file = tmpdir.join('new_version.rdf')
    shutil.copy(Path('tests/test_data/subdivisions_sh_ds/data/v2/subdivisions-skos.rdf'), new_version_file)
    return old_version_file, new_version_file


@pytest.fixture()
def metadata(tmpdir, files):
    """mandatory descriptive metadata."""
    metadata = {
        'basedir': tmpdir.mkdir('basedir'),
        'filename': 'subdivisions-skos',
        'endpoint': RDF_DIFFER_ENDPOINT_SERVICE ,
        'dataset': 'subdiv',
        'scheme_uri': 'http://publications.europa.eu/resource/authority/subdivision',
        'old_version_file': files[0],
        'old_version_id': 'v1',
        'new_version_file': files[1],
        'new_version_id': 'v2'
    }

    return metadata


@scenario('../features/diffing_two_dataset_versions.feature', 'Diffing two dataset versions')
def test_diffing_two_dataset_versions():
    """Diffing two dataset versions."""


@scenario('../features/diffing_two_dataset_versions.feature', 'Controlling the mandatory descriptive metadata')
def test_controlling_the_mandatory_descriptive_metadata():
    """Controlling the mandatory descriptive metadata."""


@given('old and new version RDF files')
def old_and_new_version_rdf_files():
    pass


@given('mandatory descriptive metadata')
def mandatory_descriptive_metadata():
    pass


@when('the user runs the diff calculator')
def the_user_runs_the_diff_calculator(metadata):
    """the user runs the diff calculator."""
    skos_history_runner = SKOSHistoryRunner(**metadata)
    skos_history_runner.run()


@then('a correct dataset folder structure is created')
def a_correct_dataset_folder_structure_is_created(metadata):
    """a correct dataset folder structure is created."""
    basedir = Path(metadata.get('basedir'))
    assert dir_exists(basedir)
    assert dir_exists(basedir / 'v1')
    assert dir_exists(basedir / 'v2')


@then('the diff calculator is executed')
def the_diff_calculator_is_executed():
    """the diff calculator is executed."""
    assert helper_fuseki_service(http_client=requests, sparql_client=SPARQLRunner()).dataset_description('subdiv')


@given('the <property> is missing or incorrect')
def the_property_is_missing_or_incorrect(metadata, property):
    """the <property> is missing or incorrect."""
    metadata[property] = ''


@when('the user runs the incomplete diff calculator')
def the_user_runs_the_incomplete_diff_calculator(metadata):
    """the user runs the diff calculator."""
    with pytest.raises(Exception) as exception:
        _ = SKOSHistoryRunner(**metadata)

    # workaround to passing the exception to the next step
    metadata['exception'] = exception


@then('an error message is generated indicating the <property> problem')
def an_error_message_is_generated_indicating_the_property_problem(metadata, property):
    """an error message is generated indicating the <property> problem."""
    assert property in str(metadata['exception'])
