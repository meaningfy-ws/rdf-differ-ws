import logging
import os
import shutil
import tempfile
import time
from pathlib import Path

from celery import Celery
from celery.worker.state import requests

from rdf_differ import config
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter
from rdf_differ.adapters.sparql import SPARQLRunner
from rdf_differ.config import RDF_DIFFER_LOGGER

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

celery_worker = Celery('rdf-differ-tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
logger = logging.getLogger(RDF_DIFFER_LOGGER)


@celery_worker.task(name="create_diff")
def async_create_diff(body: dict, old_version_file: str, new_version_file: str, cleanup_location: str):
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
    finally:
        shutil.rmtree(cleanup_location)

    logger.debug('finish async create diff')
    return True
