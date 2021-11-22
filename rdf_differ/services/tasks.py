import logging

from celery.result import AsyncResult

from rdf_differ.adapters.celery import celery_worker
from rdf_differ.config import RDF_DIFFER_LOGGER

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def retrieve_active_tasks(worker=None) -> dict:
    worker = worker if worker else celery_worker
    inspector = worker.control.inspect()

    return inspector.active()


def retrieve_task(task_id: str, worker=None) -> AsyncResult:
    worker = worker if worker else celery_worker
    task = AsyncResult(task_id, app=worker)

    return task


def revoke_task(task_id: str, terminate: bool = False, worker=None) -> str:
    worker = worker if worker else celery_worker

    worker.control.revoke(task_id, terminate=terminate)

    return 'ok'
