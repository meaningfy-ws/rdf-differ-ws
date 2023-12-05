#!/usr/bin/python3

# diffs.py
# Date: 30/07/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
import logging
from distutils.util import strtobool
from json import dumps

import requests
from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from flask import send_file
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import Conflict, InternalServerError, NotFound, UnprocessableEntity, NotAcceptable

from rdf_differ import config
from rdf_differ.adapters.celery import async_create_diff, async_generate_report
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.adapters.redis import redis_client, push_task_to_queue
from rdf_differ.adapters.sparql import SPARQLRunner
from rdf_differ.config import RDF_DIFFER_LOGGER, RDF_DIFFER_REPORTS_DB
from rdf_differ.services.ap_manager import ApplicationProfileManager
from rdf_differ.services.queue import kill_task
from rdf_differ.services.report_handling import report_exists, retrieve_report, remove_all_reports, get_all_reports, \
    read_meta_file, build_dataset_reports_location, find_dataset_name_by_id
from rdf_differ.services.tasks import retrieve_task, retrieve_active_tasks, flatten_active_tasks
from rdf_differ.utils.file_utils import save_files, build_unique_name, check_dataset_name_validity

"""
The definition of the API endpoints

Important distinction:
- dataset_name is the name of the dataset, which is the name of the folder containing the dataset diff results
- dataset_id is the uid used for both identifying the dataset and the task that is associated with its creation
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
        response = [fuseki_adapter.dataset_description(dataset) for dataset in datasets]
        logger.debug('finish get diffs endpoint')
        response = sorted(response, key=lambda x: x.get('diff_date',''), reverse=True)
        return response, 200
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
    logger.debug(f'get diff for {dataset_id} endpoint')
    try:
        meta = read_meta_file(
            build_dataset_reports_location(find_dataset_name_by_id(dataset_id),
                                           RDF_DIFFER_REPORTS_DB))
    except Exception as e:
        exception_text = f'<{dataset_id}> does not exist.'
        logger.exception(exception_text)
        raise NotFound(exception_text)  # 404

    try:
        dataset = FusekiDiffAdapter(config.RDF_DIFFER_FUSEKI_SERVICE, http_client=requests,
                                    sparql_client=SPARQLRunner()).dataset_description(meta.get('dataset_name'))
        dataset['available_reports'] = get_all_reports(meta.get('dataset_name'), config.RDF_DIFFER_REPORTS_DB)
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
          "dataset_name": "string",
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

    if not check_dataset_name_validity(body.get('dataset_name')):
        raise Conflict(f'<{body.get("dataset_name")}> name is not acceptable is not empty.'
                       'Dataset name can contain only ASCII letters, numbers, _, :, and -')  # 409

    dataset_name = build_unique_name(body.get('dataset_name'))
    body['dataset_name'] = dataset_name
    try:
        dataset = fuseki_adapter.dataset_description(dataset_name=body.get('dataset_name'))
        # if description is {} (empty) then we can create the diff
        can_create = not bool(dataset)
        logger.debug(f'dataset exists. empty: {not can_create}')
    except EndPointNotFound:
        fuseki_adapter.create_dataset(dataset_name=body.get('dataset_name'))
        can_create = True
        logger.info('creating dataset')

    if can_create:
        try:
            with save_files(old_version_file_content, new_version_file_content,
                            config.RDF_DIFFER_FILE_DB) as \
                    (db_location, old_version_file, new_version_file):
                task = async_create_diff.delay(dataset_name, body, old_version_file, new_version_file, db_location,
                                               RDF_DIFFER_REPORTS_DB)
                push_task_to_queue(dumps([task.id, dataset_name]))

                redis_client.set(task.id, str(False))
            logger.debug(f'task executed with id: {task.id}')
            return {'uid': task.id, 'dataset_name': dataset_name}, 200
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
            find_dataset_name_by_id(dataset_id))
        remove_all_reports(find_dataset_name_by_id(dataset_id), RDF_DIFFER_REPORTS_DB)

        logger.info(f'finish delete dataset: {dataset_id} endpoint')
        return f'<{dataset_id}> deleted successfully.', 200
    except (FusekiException, FileNotFoundError):
        exception_text = f'<{dataset_id}> does not exist.'
        logger.exception(exception_text)
        raise NotFound(exception_text)  # 404


def build_report(body: dict) -> tuple:
    """
        Generate a dataset diff report
    :param body:
        {
          "dataset_id": "string", // The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
          "application_profile": "string", // The application profile identifier
          "template_type": "string", // The template type identifier.
          "rebuild": "string" // flag to signal rebuilding the report even if already exists
          }
    :return: report as attachment
    :rtype: file, int
    """
    dataset_id = body['dataset_id']
    application_profile = body['application_profile']
    template_type = body['template_type']
    rebuild = strtobool(body.get('rebuild', 'false'))

    logger.debug(f'start build report for {dataset_id} endpoint')

    dataset, _ = get_diff(dataset_id)  # potential 404

    ap_manager = ApplicationProfileManager(application_profile=application_profile, template_type=template_type)
    try:
        template_location = ap_manager.get_template_folder()
        query_files = ap_manager.get_queries_dict()
    except (LookupError, FileNotFoundError) as e:
        logger.exception(str(e))
        raise UnprocessableEntity("Check valid application profiles and their template types through the API"
                                  "and if the queries folder exists in the chosen application profile folder")

    if not report_exists(find_dataset_name_by_id(dataset_id), application_profile, template_type,
                         RDF_DIFFER_REPORTS_DB) or rebuild:
        task = async_generate_report.delay(dataset_name=find_dataset_name_by_id(dataset_id),
                                           application_profile=application_profile, template_type=template_type,
                                           db_location=RDF_DIFFER_REPORTS_DB, template_location=str(template_location),
                                           query_files=query_files, dataset=dataset)
        return {'task_id': task.id, 'application_profile': application_profile}, 200
    else:
        return {'message': 'Report already exists. To rebuild send the `rebuild` query parameter set to true'}, 406


def get_report(dataset_id: str, application_profile: str, template_type: str) -> tuple:
    """
        Get a dataset diff report
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :param application_profile: The application profile identifier. This should be a text string
    :param template_type: The template type identifier. This should be a text string
    :return: html report as attachment
    :rtype: file, int
    """
    logger.debug(f'start get report for {dataset_id} endpoint')

    dataset, _ = get_diff(dataset_id)  # potential 404

    ap_manager = ApplicationProfileManager(application_profile=application_profile, template_type=template_type)
    try:
        _ = ap_manager.get_template_folder()
        _ = ap_manager.get_queries_dict()
    except (LookupError, FileNotFoundError) as e:
        logger.exception(str(e))
        raise UnprocessableEntity("Check valid application profiles and their template types through the API"
                                  "and if the queries folder exists in the chosen application profile folder")

    if report_exists(find_dataset_name_by_id(dataset_id), application_profile, template_type, RDF_DIFFER_REPORTS_DB):
        return send_file(retrieve_report(find_dataset_name_by_id(dataset_id), application_profile, template_type,
                                         RDF_DIFFER_REPORTS_DB),
                         as_attachment=True)  # 200
    else:
        raise NotFound('First send a request to build the report.')


def get_application_profiles_details() -> tuple:
    """
      Get all available application profiles and their available template variants.
    :return: list[dict]
    :rtype: list, int
    """
    return [{"application_profile": ap,
             "template_variations": ApplicationProfileManager(ap).list_template_variants()} for ap in
            ApplicationProfileManager().list_aps()], 200


def get_active_tasks() -> tuple:
    """
    Get all active celery tasks
    :return: dict of celery workers and their active tasks
    """
    logger.debug('get active tasks')
    try:
        tasks = retrieve_active_tasks()
        flattened_tasks = tasks.get(list(tasks.keys())[0], [])
    except AttributeError:
        return [], 200
    return flattened_tasks, 200


def get_task_status(task_id: str) -> tuple:
    """
    Get specified task status data
    :param task_id: Id of task to get status for
    :return: dict
    """
    logger.debug(f'get task status: {task_id}')
    task = retrieve_task(task_id)
    if task:
        try:
            result = dumps(task.result)
        except TypeError:
            result = ''

        data = {
            'task_id': task.id,
            'status': task.status,
            'result': result
        }
        return data, 200

    raise NotFound(f'Task with {task_id} doesn\'t exist')  # 404


def stop_running_task(task_id: str) -> tuple:
    """
    Revoke a task
    :param task_id: Id of task to revoke
    """
    logger.debug(f'stop task: {task_id}')
    try:
        tasks = flatten_active_tasks(retrieve_active_tasks())
        task = next(task for task in tasks if task["id"] == task_id)
        kill_task(task, RDF_DIFFER_REPORTS_DB)
    except:
        raise NotAcceptable('task already finished executing or does not exist')  # 406

    return {'message': f'task {task_id} set for revoking.'}, 200
