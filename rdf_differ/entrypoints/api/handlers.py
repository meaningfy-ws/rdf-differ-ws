#!/usr/bin/python3

# diffs.py
# Date: 30/07/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

import tempfile
from json import dumps
from pathlib import Path
from shutil import copytree

import requests
from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from eds4jinja2.builders.report_builder import ReportBuilder
from flask import send_from_directory
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import BadRequest, Conflict, InternalServerError, NotFound

from rdf_differ import config
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.adapters.skos_history_wrapper import SubprocessFailure
from rdf_differ.adapters.sparql import SPARQLRunner
from utils.file_utils import temporarily_save_files


def get_diffs() -> tuple:
    """
        List the existent datasets with their descriptions.
    :return: list of existent datasets
    :rtype: list, int
    """
    fuseki_adapter = FusekiDiffAdapter(config.ENDPOINT, http_client=requests, sparql_client=SPARQLRunner())
    try:
        datasets = fuseki_adapter.list_datasets()
        return [fuseki_adapter.dataset_description(dataset) for dataset in datasets], 200
    except (FusekiException, ValueError, IndexError) as exception:
        raise InternalServerError(str(exception))  # 500


def get_diff(dataset_id: str) -> tuple:
    """
        Get the dataset description
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :return: dataset description
    :rtype: dict, int
    """
    try:
        dataset = FusekiDiffAdapter(config.ENDPOINT, http_client=requests,
                                    sparql_client=SPARQLRunner()).dataset_description(dataset_id)
        return dataset, 200
    except EndPointNotFound:
        raise NotFound(f'<{dataset_id}> does not exist.')  # 404
    except (ValueError, IndexError):
        raise InternalServerError('Unexpected Error.')  # 500


def create_diff(body: dict, old_version_file_content: FileStorage, new_version_file_content: FileStorage) -> tuple:
    """
        Create a diff based on the versions send with old_Version_file_content and new_version_file_content.
    :param body:
        {
          "dataset_description": "string",
          "dataset_id": "string",
          "dataset_uri": "string",
          "new_version_id": "string",
          "old_version_id": "string",
        }
    :param old_version_file_content: The content of the old version file.
    :param new_version_file_content: The content of the new version file.
    :return:
    :rtype: dict, int
    """
    fuseki_adapter = FusekiDiffAdapter(config.ENDPOINT, http_client=requests, sparql_client=SPARQLRunner())

    try:
        dataset = fuseki_adapter.dataset_description(dataset_name=body.get('dataset_id'))
        # if description is {} (empty) then we can create the diff
        can_create = not bool(dataset)
    except EndPointNotFound:
        fuseki_adapter.create_dataset(dataset_name=body.get('dataset_id'))
        can_create = True

    if can_create:
        try:
            print(old_version_file_content)
            with temporarily_save_files(old_version_file_content, new_version_file_content) as \
                    (temp_dir, old_version_file, new_version_file):
                fuseki_adapter.create_diff(dataset=body.get('dataset_id'),
                                           dataset_uri=body.get('dataset_uri'),
                                           temp_dir=temp_dir,
                                           old_version_id=body.get('old_version_id'),
                                           new_version_id=body.get('new_version_id'),
                                           old_version_file=old_version_file,
                                           new_version_file=new_version_file)

            # TODO: return dataset url, in case that this call could take more time that usual api request.
            return 'Request to create a new dataset diff successfully accepted for processing.', 200
        except ValueError as exception:
            raise BadRequest(str(exception))  # 400
        except SubprocessFailure as exception:
            raise InternalServerError('Internal error while uploading the diffs.\n' + str(exception))  # 500
    else:
        raise Conflict('Dataset is not empty.')  # 409


def delete_diff(dataset_id: str) -> tuple:
    """
        Delete a dataset
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :return: info about deletion
    :rtype: str, int
    """
    try:
        FusekiDiffAdapter(config.ENDPOINT, http_client=requests, sparql_client=SPARQLRunner()).delete_dataset(
            dataset_id)
        return f'<{dataset_id}> created successfully.', 200
    except FusekiException:
        raise NotFound(f'<{dataset_id}> does not exist.')  # 404


def get_report(dataset_id: str, dataset_url: str) -> tuple:
    """
    """
    # is there a better way to check if diff exists?
    get_diff(dataset_id)  # here it can return 404

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            copytree(Path.cwd() / 'resources/eds_templates', temp_dir, dirs_exist_ok=True)
            with open(Path(temp_dir) / 'config.json', 'w') as config_file:
                config = {
                    "template": "main.html",
                    "conf":
                        {
                            "default_endpoint": dataset_url,
                            "title": "Dataset Diff Report",
                            "type": "report"
                        }
                }
                config_file.write(dumps(config))

            rp = ReportBuilder(target_path=temp_dir,
                               output_path=temp_dir)
            rp.make_document()

            return send_from_directory(Path(str(temp_dir)) / 'output', 'main.html', as_attachment=True)
    except Exception as e:
        raise InternalServerError(str(e))  # 500
