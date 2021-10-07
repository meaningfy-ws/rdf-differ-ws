#!/usr/bin/python3

# diffs.py
# Date: 30/07/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
import logging

import requests
from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from flask import send_file
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import Conflict, InternalServerError, NotFound, UnprocessableEntity

from rdf_differ import config
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.adapters.sparql import SPARQLRunner
from rdf_differ.config import RDF_DIFFER_LOGGER, RDF_DIFFER_REPORTS_DB
from rdf_differ.services.report_handling import report_exists, retrieve_report
from rdf_differ.services.tasks import async_create_diff, retrieve_task, retrieve_active_tasks, async_generate_report
from rdf_differ.services.validation import validate_choice
from utils.file_utils import save_files

"""
The definition of the API endpoints
"""
logger = logging.getLogger(RDF_DIFFER_LOGGER)


def get_diffs() -> tuple:
    """
        List the existent datasets with their descriptions.
    :return: list of existent datasets
    :rtype: list, int
    """
    logger.debug('start get diffs endpoint')

    fuseki_adapter = FusekiDiffAdapter(config.RDF_DIFFER_FUSEKI_SERVICE, http_client=requests,
                                       sparql_client=SPARQLRunner())
    try:
        datasets = fuseki_adapter.list_datasets()
        logger.debug('finish get diffs endpoint')
        return [fuseki_adapter.dataset_description(dataset) for dataset in datasets], 200
    except (FusekiException, ValueError, IndexError) as exception:
        logger.exception(str(exception))
        raise InternalServerError(str(exception))  # 500


def get_diff(dataset_id: str) -> tuple:
    """
        Get the dataset description
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :return: dataset description
    :rtype: dict, int
    """
    logger.debug(f'start get diff for {dataset_id} endpoint')

    try:
        dataset = FusekiDiffAdapter(config.RDF_DIFFER_FUSEKI_SERVICE, http_client=requests,
                                    sparql_client=SPARQLRunner()).dataset_description(dataset_id)
        logger.debug(f'finish get diff for {dataset_id} endpoint')
        return dataset, 200
    except EndPointNotFound:
        exception_text = f'<{dataset_id}> does not exist.'
        logger.exception(exception_text)
        raise NotFound(exception_text)  # 404
    except (ValueError, IndexError) as exception:
        exception_text = f'Unexpected Error. {str(exception)}'
        logger.exception(exception_text)
        raise InternalServerError(exception_text)  # 500


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
    logger.debug('start create diff endpoint')

    fuseki_adapter = FusekiDiffAdapter(config.RDF_DIFFER_FUSEKI_SERVICE, http_client=requests,
                                       sparql_client=SPARQLRunner())

    try:
        dataset = fuseki_adapter.dataset_description(dataset_name=body.get('dataset_id'))
        # if description is {} (empty) then we can create the diff
        can_create = not bool(dataset)
        logger.debug('dataset exists, but is empty')
    except EndPointNotFound:
        fuseki_adapter.create_dataset(dataset_name=body.get('dataset_id'))
        can_create = True
        logger.debug('creating dataset')

    if can_create:
        try:
            with save_files(old_version_file_content, new_version_file_content,
                            config.RDF_DIFFER_FILE_DB) as \
                    (db_location, old_version_file, new_version_file):
                task = async_create_diff.delay(body, old_version_file, new_version_file, db_location)
            logger.debug('finish create diff endpoint')
            return {'task_id': task.id}, 200
        except ValueError as exception:
            exception_text = 'Internal error while uploading the diffs.\n' + str(exception)
            logger.exception(exception_text)
            raise InternalServerError(exception_text)  # 500
    else:
        logger.exception('dataset exists and is not empty, no diff created')
        raise Conflict('Dataset is not empty.')  # 409


def delete_diff(dataset_id: str) -> tuple:
    """
        Delete a dataset
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :return: info about deletion
    :rtype: str, int
    """
    logger.debug(f'start delete dataset: {dataset_id} endpoint')

    try:
        FusekiDiffAdapter(config.RDF_DIFFER_FUSEKI_SERVICE, http_client=requests,
                          sparql_client=SPARQLRunner()).delete_dataset(
            dataset_id)
        logger.debug(f'finish delete dataset: {dataset_id} endpoint')
        return f'<{dataset_id}> deleted successfully.', 200
    except FusekiException:
        exception_text = f'<{dataset_id}> does not exist.'
        logger.exception(exception_text)
        raise NotFound(exception_text)  # 404


def get_report(dataset_id: str, application_profile: str = "diff_report", rebuild: bool = False) -> tuple:
    """
        Generate a dataset diff report
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :param application_profile: The application profile identifier. This should be a text string
    :param rebuild: flag to signal rebuilding the report even if already exists
    :return: html report as attachment
    :rtype: file, int
    """
    logger.debug(f'start get report for {dataset_id} endpoint')

    dataset, _ = get_diff(dataset_id)  # potential 404

    is_valid, exception_text = validate_choice(application_profile, config.RDF_DIFFER_APPLICATION_PROFILES_LIST)
    if not is_valid:
        raise UnprocessableEntity(exception_text)

    if not report_exists(dataset_id, application_profile, RDF_DIFFER_REPORTS_DB) or rebuild:
        task = async_generate_report.delay(dataset, application_profile)
        return {'task_id': task.id}, 200
    else:
        return send_file(retrieve_report(dataset_id, application_profile, RDF_DIFFER_REPORTS_DB),
                         as_attachment=True)  # 200


def get_active_tasks() -> tuple:
    """
    Get all active celery tasks
    :return: dict of celery workers and their active tasks
    """
    tasks = retrieve_active_tasks()
    return tasks, 200


def get_task_status(task_id: str) -> tuple:
    """
    Get specified task status data
    :param task_id: Id of task to get status for
    :return: dict
    """
    task = retrieve_task(task_id)
    if task:
        return {
                   "task_id": task.id,
                   "task_status": task.status,
               }, 200
    raise NotFound('task not found')  # 404
