#!/usr/bin/python3

# api_wrapper.py
# Date:  18/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Service to consume RDF diff API.
"""
import requests
from werkzeug.datastructures import FileStorage

from rdf_differ.entrypoints.ui import config


def get_datasets() -> tuple:
    """
    Method to connect to the RDF diff api to get all dataset diffs
    :return: the list of dataset diffs
    :rtype: list, int
    """
    response = requests.get(config.RDF_DIFF_API_ENDPOINT + '/diffs')
    return response.json(), response.status_code


def get_dataset(dataset_id: str) -> tuple:
    """
    Method to connect to the RDF diff api to get the dataset diff
    :param dataset_id: The dataset identifier.
    :return: dataset description (as specified in the rdf_differ.adapters.diff_adapter.py)
    :rtype: dict, int
    """
    response = requests.get(config.RDF_DIFF_API_ENDPOINT + '/diffs/' + dataset_id)
    return response.json(), response.status_code


def create_diff(dataset_name: str, dataset_description: str, dataset_uri: str,
                old_version_id: str, old_version_file: FileStorage,
                new_version_id: str, new_version_file: FileStorage) -> tuple:
    """
    Method to connect to the RDF diff api to create a dataset diff
    :param dataset_name: The dataset identifier.
    :param dataset_description: Description of the dataset diff (currently not used nor saved)
    :param dataset_uri: the concept scheme or dataset URI
    :param old_version_id: name used for diff creation
    :param old_version_file: the location of the file to be created
    :param new_version_id: name used for diff creation
    :param new_version_file: the location of the file to be created
    :return: state of the api response
    :rtype: str, int
    """
    files = {
        'old_version_file_content': (old_version_file.filename, old_version_file.stream, old_version_file.mimetype),
        'new_version_file_content': (new_version_file.filename, new_version_file.stream, new_version_file.mimetype),
    }
    data = {
        'dataset_id': dataset_name,
        'dataset_description': dataset_description,
        'dataset_uri': dataset_uri,
        'old_version_id': old_version_id,
        'new_version_id': new_version_id
    }
    response = requests.post(config.RDF_DIFF_API_ENDPOINT + '/diffs', data=data, files=files)
    return response.text, response.status_code
