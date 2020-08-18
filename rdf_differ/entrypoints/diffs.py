#!/usr/bin/python3

# diffs.py
# Date: 30/07/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

import requests
from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import Conflict, InternalServerError, BadRequest

from rdf_differ import config
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.adapters.skos_history_wrapper import SubprocessFailure
from rdf_differ.adapters.sparql import SPARQLRunner
from utils.file_utils import temporarily_save_files


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
    fuseki_adapter = FusekiDiffAdapter(config.ENDPOINT, http_requests=requests, sparql_requests=SPARQLRunner())

    try:
        dataset = fuseki_adapter.dataset_description(dataset_name=body.get('dataset_id'))
        # if description is {} (empty) then we can create the diff
        can_create = not bool(dataset)
    except EndPointNotFound:
        can_create = True

    if can_create:
        try:
            with temporarily_save_files(old_version_file_content, new_version_file_content) as \
                    (temp_dir, old_version_file, new_version_file):
                fuseki_adapter.create_diff(dataset=body.get('dataset_id'),
                                           dataset_uri=body.get('dataset_uri'),
                                           temp_dir=temp_dir,
                                           old_version_id=body.get('old_version_id'),
                                           new_version_id=body.get('new_version_id'),
                                           old_version_file=old_version_file,
                                           new_version_file=new_version_file)

            return {'detail': 'Request to create a new dataset diff successfully accepted for processing.'}, 200
        except ValueError as exception:
            raise BadRequest(str(exception))  # 400
        except SubprocessFailure:
            raise InternalServerError('Internal error while uploading the diffs.')  # 500
    else:
        raise Conflict('Dataset is not empty.')  # 409


def get_diffs() -> tuple:
    """
        List the existent datasets with their descriptions.
    :return: list of existent datasets
    :rtype: list, int
    """
    fuseki_adapter = FusekiDiffAdapter(config.ENDPOINT, http_requests=requests, sparql_requests=SPARQLRunner())
    try:
        datasets, status = fuseki_adapter.list_datasets()
        return [{dataset: fuseki_adapter.dataset_description(dataset)} for dataset in datasets], status
    except FusekiException as exception:
        return str(exception), 500


def get_diff(dataset_id: str) -> tuple:
    """
        Get the dataset description
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :return: dataset description
    :rtype: dict, int
    """
    try:
        return FusekiDiffAdapter(config.ENDPOINT, http_requests=requests,
                                 sparql_requests=SPARQLRunner()).dataset_description(dataset_id)
    except EndPointNotFound:
        return f'<{dataset_id}> does not exist.', 404
    # TODO: improve on the type of the error catching
    except Exception:
        return "Unexpected Error.", 500


def delete_diff(dataset_id: str) -> tuple:
    """
        Delete a dataset
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :return: info about deletion
    :rtype: str, int
    """
    return FusekiDiffAdapter(config.ENDPOINT, http_requests=requests, sparql_requests=SPARQLRunner()) \
        .delete_dataset(dataset_id)
