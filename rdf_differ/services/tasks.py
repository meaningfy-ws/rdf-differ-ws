import logging
import shutil
from pathlib import Path

import requests
from celery.result import AsyncResult

from rdf_differ import config
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.adapters.sparql import SPARQLRunner
from rdf_differ.config import celery_worker, RDF_DIFFER_LOGGER

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def retrieve_active_tasks(worker=None) -> list:
    worker = worker if worker else celery_worker
    inspector = worker.control.inspect()

    return inspector.active()


def retrieve_task(task_id: str, worker=None) -> AsyncResult:
    worker = worker if worker else celery_worker
    task = AsyncResult(task_id, app=worker)

    return task


# =================== TASKS =================== #
@celery_worker.task(name="create_diff")
def async_create_diff(body: dict, old_version_file: str, new_version_file: str, cleanup_location: str):
    """
    Task that retrieves diff files form specified location, creates the diff and cleans up the files
    :param body: data for diff creation
    :param old_version_file: location of the old version file
    :param new_version_file: location of the new version file
    :param cleanup_location: location to cleanup
    """
    logger.debug('start async create diff')
    fuseki_adapter = FusekiDiffAdapter(config.RDF_DIFFER_FUSEKI_SERVICE, http_client=requests,
                                       sparql_client=SPARQLRunner())
    try:
        fuseki_adapter.create_diff(dataset=body.get('dataset_id'),
                                   dataset_uri=body.get('dataset_uri'),
                                   temp_dir=Path(cleanup_location),
                                   old_version_id=body.get('old_version_id'),
                                   new_version_id=body.get('new_version_id'),
                                   old_version_file=Path(old_version_file),
                                   new_version_file=Path(new_version_file))
    except Exception as e:
        logger.error(str(e))
        raise FusekiException(str(e))
    finally:
        shutil.rmtree(cleanup_location)

    logger.debug('finish async create diff')
    return True
