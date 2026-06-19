import logging
import shutil
import tempfile
from pathlib import Path
from typing import cast

import requests
from celery import Celery

from rdf_differ import config
from rdf_differ.core.adapters.filesystem import build_dataset_reports_location
from rdf_differ.core.adapters.sparql import SPARQLRunner
from rdf_differ.core.domain.time import get_timestamp
from rdf_differ.diffing.adapters.diff_adapter import FusekiDiffAdapter
from rdf_differ.diffing.adapters.exceptions import FusekiException
from rdf_differ.loader.adapters.graph_store_provider import build_graph_store
from rdf_differ.loader.adapters.settings import StoreSettings
from rdf_differ.loader.adapters.skolemizer import strategy_for
from rdf_differ.loader.domain.model import Engine
from rdf_differ.loader.services.diff_service import build_diff_config, create_version_diff
from rdf_differ.reporting.services.report_handling import (
    build_report,
    generate_meta_file,
    save_report,
)

celery_worker = Celery(
    "rdf-differ-tasks",
    broker=config.RDF_DIFFER_REDIS_SERVICE,
    backend=config.RDF_DIFFER_REDIS_SERVICE,
)
celery_worker.conf.update(result_extended=True)

logger = logging.getLogger(config.RDF_DIFFER_LOGGER)

CELERY_CREATE_DIFF = "create_diff"
CELERY_GENERATE_REPORT = "generate_report"


def _create_diff_with_python_loader(
    *, dataset: str, dataset_uri: str, old_id: str, new_id: str, old_file: str, new_file: str
) -> None:
    """Create the diff via the Python RDF Loading Module (RemoteSparqlStore).

    Composition root for the remote path: builds the per-dataset ``StoreSettings``
    + remote store + blank-node strategy, then delegates to the pure diff service.
    Replaces the ``load_versions.sh`` subprocess when ``RDF_DIFFER_USE_PYTHON_LOADER``
    is enabled.
    """
    base = config.RDF_DIFFER_FUSEKI_SERVICE
    settings = StoreSettings(
        username=config.RDF_DIFFER_FUSEKI_USERNAME,
        password=config.RDF_DIFFER_FUSEKI_PASSWORD,
        data_endpoint_override=f"{base}/{dataset}/data",
        update_endpoint_override=f"{base}/{dataset}",
        query_endpoint_override=f"{base}/{dataset}/query",
    )
    store = build_graph_store(Engine.REMOTE, settings)
    cfg = build_diff_config(
        dataset=dataset,
        scheme_uri=dataset_uri,
        old_version_id=old_id,
        new_version_id=new_id,
        old_version_file=old_file,
        new_version_file=new_file,
        engine=Engine.REMOTE,
    )
    create_version_diff(
        store,
        cfg,
        blank_node_strategy=strategy_for(cfg.blank_node_policy, base_iri=cfg.scheme_uri),
        query_endpoint=settings.query_endpoint,
    )


# =================== TASKS =================== #
# bind=True means that the task will be bound to the current context
@celery_worker.task(name=CELERY_CREATE_DIFF, bind=True)
def async_create_diff(
    self,
    dataset_id: str,
    body: dict,
    old_version_file: str,
    new_version_file: str,
    cleanup_location: str,
    reports_location: str,
):
    """
    Task that retrieves diff files form specified location, creates the diff and cleans up the files

    NOTE: the order of the first arg is important for task cancellation, don't change its order
    :param dataset_id: name of the dataset
    :param body: data for diff creation
    :param old_version_file: location of the old version file
    :param new_version_file: location of the new version file
    :param cleanup_location: location to cleanup
    :param reports_location: location to store dataset reports
    """
    logger.debug("start async create diff")
    fuseki_adapter = FusekiDiffAdapter(
        config.RDF_DIFFER_FUSEKI_SERVICE, http_client=requests, sparql_client=SPARQLRunner()
    )

    try:
        if config.RDF_DIFFER_USE_PYTHON_LOADER:
            _create_diff_with_python_loader(
                dataset=dataset_id,
                dataset_uri=cast(str, body.get("dataset_uri")),
                old_id=cast(str, body.get("old_version_id")),
                new_id=cast(str, body.get("new_version_id")),
                old_file=old_version_file,
                new_file=new_version_file,
            )
        else:
            fuseki_adapter.create_diff(
                dataset=dataset_id,
                dataset_uri=cast(str, body.get("dataset_uri")),
                temp_dir=Path(cleanup_location),
                old_version_id=cast(str, body.get("old_version_id")),
                new_version_id=cast(str, body.get("new_version_id")),
                old_version_file=Path(old_version_file),
                new_version_file=Path(new_version_file),
            )
        fuseki_adapter.inject_metadata(dataset_name=dataset_id, metadata=body)
    except Exception as e:
        logger.error(str(e))
        raise FusekiException(str(e))
    finally:
        shutil.rmtree(cleanup_location)

    dataset_location = Path(build_dataset_reports_location(dataset_id, reports_location))
    dataset_location.mkdir(parents=True, exist_ok=True)
    generate_meta_file(
        reports_location=str(dataset_location), uid=self.request.id, dataset_name=dataset_id
    )
    logger.debug("finish async create diff")
    return True


@celery_worker.task(name=CELERY_GENERATE_REPORT, bind=True)
def async_generate_report(
    self,
    dataset_name: str,
    application_profile: str,
    template_type: str,
    db_location: str,
    template_location: str,
    query_files: dict,
    dataset: dict,
):
    """
    Task that generates the specified diff report

    NOTE: the order of the first 4 args is important for task cancellation, don't change its order
    :param dataset_name: name of the dataset
    :param application_profile: the application profile for report generation
    :param template_type: the application profile report "flavour"
    :param template_location:
    :param query_files: list of files to be included in the generation
    :param dataset: The dataset data
    :param db_location: location of the local db storage
    """
    timestamp = get_timestamp()
    with tempfile.TemporaryDirectory() as temp_dir:
        path_to_report = build_report(
            str(temp_dir),
            template_location,
            query_files,
            application_profile,
            dataset_name,
            dataset,
            timestamp,
        )
        save_report(
            path_to_report,
            dataset["dataset_name"],
            application_profile,
            template_type,
            timestamp,
            db_location,
        )

    return True
