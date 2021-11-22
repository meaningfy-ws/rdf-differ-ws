import logging
import shutil
import tempfile
from pathlib import Path

import requests
from celery import Celery

from rdf_differ import config
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.adapters.sparql import SPARQLRunner
from rdf_differ.config import RDF_DIFFER_LOGGER
from rdf_differ.config import RDF_DIFFER_REDIS_SERVICE
from rdf_differ.services.queue import cleanup_diff_creation, cleanup_report_creation
from rdf_differ.services.report_handling import build_report, save_report

celery_worker = Celery('rdf-differ-tasks', broker=RDF_DIFFER_REDIS_SERVICE, backend=RDF_DIFFER_REDIS_SERVICE)
celery_worker.conf.update(result_extended=True)

logger = logging.getLogger(RDF_DIFFER_LOGGER)


# =================== TASKS =================== #
@celery_worker.task(name="create_diff", bind=True)
def async_create_diff(self, body: dict, old_version_file: str, new_version_file: str, cleanup_location: str):
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

    import time
    time.sleep(20)
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

    if cleanup_diff_creation(body.get('dataset_id'), self.request.id):
        return False

    logger.debug('finish async create diff')
    return True


@celery_worker.task(name="generate_report", bind=True)
def async_generate_report(self, template_location: str, query_files: dict, dataset: dict, application_profile: str,
                          template_type: str, db_location: str):
    """
    Task that generates the specified diff report
    :param template_location:
    :param query_files: list of files to be included in the generation
    :param dataset: The dataset data
    :param application_profile: the application profile for report generation
    :param template_type: the application profile report "flavour"
    :param db_location: location of the local db storage
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        path_to_report = build_report(str(temp_dir), template_location, query_files, dataset)
        save_report(path_to_report, dataset['dataset_id'], application_profile, template_type, db_location)

    if cleanup_report_creation(dataset.get('dataset_id'), application_profile, template_type, db_location,
                               self.request.id):
        logger.debug('request to revoke task received. initiating cleanup process.')
        return False
    return True
