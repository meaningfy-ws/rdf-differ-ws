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
from rdf_differ.services.report_handling import build_report, save_report
from rdf_differ.services.time import get_timestamp

celery_worker = Celery('rdf-differ-tasks', broker=RDF_DIFFER_REDIS_SERVICE, backend=RDF_DIFFER_REDIS_SERVICE)
celery_worker.conf.update(result_extended=True)

logger = logging.getLogger(RDF_DIFFER_LOGGER)

CELERY_CREATE_DIFF = 'create_diff'
CELERY_GENERATE_REPORT = 'generate_report'


# =================== TASKS =================== #
@celery_worker.task(name=CELERY_CREATE_DIFF, bind=True)
def async_create_diff(self, dataset_id: str, body: dict, old_version_file: str, new_version_file: str,
                      cleanup_location: str):
    """
    Task that retrieves diff files form specified location, creates the diff and cleans up the files

    NOTE: the order of the first arg is important for task cancellation, don't change its order
    :param dataset_id: name of the dataset
    :param body: data for diff creation
    :param old_version_file: location of the old version file
    :param new_version_file: location of the new version file
    :param cleanup_location: location to cleanup
    """
    logger.debug('start async create diff')
    fuseki_adapter = FusekiDiffAdapter(config.RDF_DIFFER_FUSEKI_SERVICE, http_client=requests,
                                       sparql_client=SPARQLRunner())

    try:
        fuseki_adapter.create_diff(dataset=dataset_id,
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


@celery_worker.task(name=CELERY_GENERATE_REPORT, bind=True)
def async_generate_report(self, dataset_id: str, application_profile: str,
                          template_type: str, db_location: str, template_location: str, query_files: dict, dataset: dict
                          ):
    """
    Task that generates the specified diff report

    NOTE: the order of the first 4 args is important for task cancellation, don't change its order
    :param dataset_id: name of the dataset
    :param application_profile: the application profile for report generation
    :param template_type: the application profile report "flavour"
    :param template_location:
    :param query_files: list of files to be included in the generation
    :param dataset: The dataset data
    :param db_location: location of the local db storage
    """
    timestamp = get_timestamp()
    with tempfile.TemporaryDirectory() as temp_dir:
        path_to_report = build_report(str(temp_dir), template_location, query_files, dataset, timestamp)
        save_report(path_to_report, dataset['dataset_id'], application_profile, template_type, timestamp, db_location)

    return True
