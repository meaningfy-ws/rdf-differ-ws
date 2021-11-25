#!/usr/bin/python3

# api_wrapper.py
# Date:  18/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Service to consume RDF diff API.
"""
import re
from json import dumps
from pathlib import Path

import requests
from werkzeug.datastructures import FileStorage

import rdf_differ.config


def get_datasets() -> tuple:
    """
    Method to connect to the RDF diff api to get all dataset diffs
    :return: the list of dataset diffs
    :rtype: list, int
    """
    response = requests.get(rdf_differ.config.RDF_DIFFER_API_SERVICE + '/diffs')
    return response.json(), response.status_code


def get_dataset(dataset_id: str) -> tuple:
    """
    Method to connect to the RDF diff api to get the dataset diff
    :param dataset_id: The dataset identifier.
    :return: dataset description (as specified in the rdf_differ.adapters.diff_adapter.py)
    :rtype: dict, int
    """
    response = requests.get(rdf_differ.config.RDF_DIFFER_API_SERVICE + f'/diffs/{dataset_id}')
    return response.json(), response.status_code


def get_report(dataset_id: str, application_profile: str, template_type: str) -> tuple:
    """
    Method to connect to the RDF diff api to get the dataset diff report
    :param dataset_id: The dataset identifier.
    :param application_profile: application profile for report
    :param template_type: report variation
    :return: html report
    :rtype: file, int
    """
    response = requests.get(url=rdf_differ.config.RDF_DIFFER_API_SERVICE + '/diffs/report',
                            params={
                                'dataset_id': dataset_id,
                                'application_profile': application_profile,
                                'template_type': template_type
                            })
    d = response.headers['content-disposition']
    file_extension = Path(re.findall("filename=(.+)", d)[0]).suffix
    return response.content, file_extension, response.status_code


def build_report(dataset_id: str, application_profile: str, template_type: str) -> tuple:
    """
    Method to send build a report call to api
    :param dataset_id: The dataset identifier.
    :param application_profile: application profile for report
    :param template_type: report variation
    :return: task and dataset ids
    """
    data = dumps({
        'dataset_id': dataset_id,
        'application_profile': application_profile,
        'template_type': template_type
    })
    headers = {'Content-type': 'application/json'}
    response = requests.post(rdf_differ.config.RDF_DIFFER_API_SERVICE + '/diffs/report', data=data, headers=headers)
    return response.text, response.status_code


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
    response = requests.post(rdf_differ.config.RDF_DIFFER_API_SERVICE + '/diffs', data=data, files=files)
    return response.text, response.status_code


def get_application_profiles() -> tuple:
    """
    Method to get application profiles from api
    :return: applicaiton profiles
    :rtype list, int
    """
    response = requests.get(url=rdf_differ.config.RDF_DIFFER_API_SERVICE + '/aps')
    return response.json(), response.status_code


def get_active_tasks() -> tuple:
    """
    Method to get celery active tasks from api
    :return: active celery tasks
    :rtype list, int
    """
    response = requests.get(url=rdf_differ.config.RDF_DIFFER_API_SERVICE + '/tasks/active')
    return response.json(), response.status_code


def revoke_task(task_id: str) -> tuple:
    """
    Method to kill celery tasks from api
    :param task_id: celery task to kill
    :return: api response
    :rtype: dict, int
    """
    response = requests.delete(url=f'{rdf_differ.config.RDF_DIFFER_API_SERVICE}/tasks/{task_id}')
    return response.json(), response.status_code
