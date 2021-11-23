import logging

import requests

from rdf_differ import config
from rdf_differ.adapters.celery import CELERY_CREATE_DIFF, CELERY_GENERATE_REPORT
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter
from rdf_differ.adapters.redis import task_exists_in_queue, push_task_to_queue
from rdf_differ.adapters.sparql import SPARQLRunner
from rdf_differ.config import RDF_DIFFER_LOGGER
from rdf_differ.services.report_handling import remove_report
from rdf_differ.services.tasks import revoke_task

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def stop_task(task_id):
    """
    try to add task into the revoking queue

    :param task_id: celery task id
    """
    if not task_exists_in_queue(task_id):
        push_task_to_queue(task_id)
    else:
        raise ValueError('task already marked for revoking')


def cleanup_diff_creation(dataset_id):
    """
    undo all actions for diff creation

    :param dataset_id: dataset to clean
    """
    logger.debug('request to revoke task received. initiating cleanup process.')
    FusekiDiffAdapter(config.RDF_DIFFER_FUSEKI_SERVICE, http_client=requests,
                      sparql_client=SPARQLRunner()).delete_dataset(
        dataset_id)


def cleanup_report_creation(dataset_id, application_profile, template_type, db_location):
    """
    undo all actions for report creation

    :param dataset_id: dataset name for report identification
    :param application_profile: application profile for report identification
    :param template_type: report marked for cleanup
    :param db_location: which db to be used for cleanup
    """
    logger.debug('request to revoke task received. initiating cleanup process.')
    remove_report(dataset_id, application_profile, template_type, db_location)


def kill_task(task: dict, db_location: str):
    """
    Kill a currently running task
    :param task: task to kill
    :param db_location: which db to be used for cleanup
    :return:
    """
    revoke_task(task['id'], True)
    if task['type'] == CELERY_CREATE_DIFF:
        logger.debug('cleanup diff create')
        cleanup_diff_creation(dataset_id=task["args"][0])
    elif task['type'] == CELERY_GENERATE_REPORT:
        logger.debug('cleanup report create')
        cleanup_report_creation(task["args"][0], task["args"][1], task["args"][2], db_location)
