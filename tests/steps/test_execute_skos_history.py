# coding=utf-8
"""Running the skos-history diff of two dataset versions feature tests."""
import shutil
from pathlib import Path

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

from rdf_differ.diff_adapter import FusekiDiffAdapter
from rdf_differ.skos_history_wrapper import SKOSHistoryRunner


@scenario('../features/execute_skos_history.feature', 'Running the skos-history')
def test_running_the_skos_history():
    """Running the skos-history."""


@given("a correct dataset folder structure")
def basedir(tmpdir):
    """a correct dataset folder structure"""
    basedir = tmpdir.mkdir('basedir')
    old_version_id = basedir.mkdir('v1')
    new_version_id = basedir.mkdir('v2')

    old_version_file = old_version_id.join('subdivisions-skos.rdf')
    new_version_file = new_version_id.join('subdivisions-skos.rdf')

    shutil.copy(Path('tests/test_data/subdivisions_sh_ds/data/v1/subdivisions-skos.rdf'), old_version_file)
    shutil.copy(Path('tests/test_data/subdivisions_sh_ds/data/v2/subdivisions-skos.rdf'), new_version_file)

    return basedir


@given("a correct configuration file")
def config_location(tmpdir, basedir):
    """a correct configuration file"""
    config_content = f"""#!/bin/bash
DATASET=ds-subdivision
SCHEMEURI="http://publications.europa.eu/resource/authority/subdivision"

VERSIONS=(v1 v2)
BASEDIR={basedir}
FILENAME=subdivisions-skos.rdf

PUT_URI=http://localhost:3030/subdiv/data
UPDATE_URI=http://localhost:3030/subdiv
QUERY_URI=http://localhost:3030/subdiv/query

INPUT_MIME_TYPE="application/rdf+xml"
    """
    config_location = basedir.join('skos.config')
    config_location.write(config_content)
    return config_location


@when("the user runs the skos-history calculator")
def the_user_runs_the_skos_history_calculator(config_location):
    """the user runs the skos-history calculator"""
    SKOSHistoryRunner.execute_subprocess(config_location)


@then('the DSV description is generated')
def the_dsv_description_is_generated():
    """the DSV description is generated."""
    assert FusekiDiffAdapter(triplestore_service_url="http://localhost:3030/").diff_description('subdiv')


@then('the dataset versions are loaded into the triplestore')
def the_dataset_versions_are_loaded_into_the_triplestore():
    """the dataset versions are loaded into the triplestore."""
    diff_description, _ = FusekiDiffAdapter(triplestore_service_url="http://localhost:3030/").diff_description('subdiv')

    assert len(diff_description['dataset_versions']) == 2
    assert "v1" in diff_description['old_version_id']
    assert "v2" in diff_description['new_version_id']


@then('the insertions and deletions graphs are created')
def the_insertions_and_deletions_graphs_are_created():
    """the insertions and deletions graphs are created."""
    fuseki_service = FusekiDiffAdapter(triplestore_service_url="http://localhost:3030/")

    insertions_count, _ = fuseki_service.count_inserted_triples('subdiv')
    deletions_count, _ = fuseki_service.count_deleted_triples('subdiv')

    assert insertions_count != 0
    assert deletions_count != 0
