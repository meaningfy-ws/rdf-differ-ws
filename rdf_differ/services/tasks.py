import logging

from celery.result import AsyncResult

from rdf_differ.adapters.celery import celery_worker
from rdf_differ.config import RDF_DIFFER_LOGGER

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def flatten_active_tasks(tasks: dict) -> list:
    return tasks.get(list(tasks.keys())[0], [])


def retrieve_active_tasks(worker=None) -> dict:
    """
    Get all currently running tasks
    :param worker: which celery worker to get tasks from
    :return: active celery tasks
    """
    worker = worker if worker else celery_worker
    inspector = worker.control.inspect()

    return inspector.active()


def retrieve_task(task_id: str, worker=None) -> AsyncResult:
    """
    Get specific celery task
    :param task_id: task id to retrieve data from
    :param worker: which celery worker to get tasks from
    :return: task info
    """
    worker = worker if worker else celery_worker
    task = AsyncResult(task_id, app=worker)

    return task


def revoke_task(task_id: str, terminate: bool = False, worker=None):
    """
    Kill a thread
    :param task_id: task id to terminate
    :param terminate: whether to kill task even if it already started
    :param worker: which celery worker to get tasks from
    :return:
    """
    worker = worker if worker else celery_worker

    worker.control.revoke(task_id, terminate=terminate)
