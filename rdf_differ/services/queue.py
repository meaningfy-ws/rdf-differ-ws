import logging

import requests

from rdf_differ import config
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter
from rdf_differ.adapters.redis import task_exists_in_revoking_queue, push_task_to_revoking_queue, \
    remove_task_from_revoking_queue
from rdf_differ.adapters.sparql import SPARQLRunner
from rdf_differ.config import RDF_DIFFER_LOGGER
from rdf_differ.services.report_handling import remove_report

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def stop_task(task_id):
    if not task_exists_in_revoking_queue(task_id):
        push_task_to_revoking_queue(task_id)
    else:
        raise ValueError('task already marked for revoking')


def cleanup_diff_creation(dataset_id, task_id):
    logger.debug('request to revoke task received. initiating cleanup process.')
    if task_exists_in_revoking_queue(task_id):
        FusekiDiffAdapter(config.RDF_DIFFER_FUSEKI_SERVICE, http_client=requests,
                          sparql_client=SPARQLRunner()).delete_dataset(
            dataset_id)
        remove_task_from_revoking_queue(task_id)

        return True

    return False


def cleanup_report_creation(dataset_id, application_profile, template_type, db_location, task_id):
    logger.debug('request to revoke task received. initiating cleanup process.')
    if task_exists_in_revoking_queue(task_id):
        remove_report(dataset_id, application_profile, template_type, db_location)
        remove_task_from_revoking_queue(task_id)

        return True

    return False