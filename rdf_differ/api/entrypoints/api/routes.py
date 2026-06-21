"""REST API path operations.

FastAPI routes raising ``HTTPException`` and returning pydantic models /
responses. Orchestration calls the existing services and adapters; no
diff/report computation lives here.
"""

import logging
from http import HTTPStatus
from json import dumps
from pathlib import Path
from typing import cast

import requests
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi import Path as PathParam
from fastapi.responses import FileResponse, JSONResponse
from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from werkzeug.datastructures import FileStorage

from rdf_differ import config
from rdf_differ.api.domain.model import CreateDiffResponse, MessageResponse, ReportTaskResponse
from rdf_differ.api.entrypoints.api.schemas import ReportRequest
from rdf_differ.api.services.celery import async_create_diff, async_generate_report
from rdf_differ.api.services.queue import kill_task
from rdf_differ.api.services.tasks import flatten_active_tasks, retrieve_active_tasks, retrieve_task
from rdf_differ.core.adapters.filesystem import (
    build_dataset_reports_location,
    read_meta_file,
    save_files,
)
from rdf_differ.core.adapters.redis import push_task_to_queue, redis_client
from rdf_differ.core.adapters.sparql import SPARQLRunner
from rdf_differ.core.domain import strtobool
from rdf_differ.core.domain.naming import build_unique_name, check_dataset_name_validity
from rdf_differ.diffing.adapters.diff_adapter import FusekiDiffAdapter
from rdf_differ.diffing.adapters.exceptions import FusekiException
from rdf_differ.reporting.services.ap_manager import ApplicationProfileManager
from rdf_differ.reporting.services.report_handling import (
    find_dataset_name_by_id,
    get_all_reports,
    remove_all_reports,
    report_exists,
    retrieve_report,
)

logger = logging.getLogger(config.RDF_DIFFER_LOGGER)
router = APIRouter()


def _fuseki_adapter() -> FusekiDiffAdapter:
    return FusekiDiffAdapter(
        config.RDF_DIFFER_FUSEKI_SERVICE, http_client=requests, sparql_client=SPARQLRunner()
    )


@router.get("/diffs")
def list_diffs() -> list:
    """List the existent datasets with their descriptions."""
    logger.debug("start get diffs endpoint")
    adapter = _fuseki_adapter()
    try:
        datasets = adapter.list_datasets()
        response = [adapter.dataset_description(dataset) for dataset in datasets]
        response = sorted(response, key=lambda x: x.get("diff_date", ""), reverse=True)
        return response
    except (FusekiException, ValueError, IndexError) as exception:
        logger.exception(str(exception))
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, str(exception)) from exception


@router.post("/diffs")
def create_diff(
    dataset_name: str = Form(...),
    dataset_uri: str = Form(...),
    old_version_id: str = Form(...),
    new_version_id: str = Form(...),
    old_version_file_content: UploadFile = File(...),
    new_version_file_content: UploadFile = File(...),
    dataset_description: str = Form(""),
) -> CreateDiffResponse:
    """Create a diff between the two uploaded dataset versions."""
    logger.debug("start create diff endpoint")
    adapter = _fuseki_adapter()

    if not check_dataset_name_validity(dataset_name):
        raise HTTPException(
            HTTPStatus.CONFLICT,
            f"<{dataset_name}> name is not acceptable is not empty."
            "Dataset name can contain only ASCII letters, numbers, _, :, and -",
        )

    old_file = _as_file_storage(old_version_file_content)
    new_file = _as_file_storage(new_version_file_content)
    unique_name = build_unique_name(dataset_name)
    body = {
        "dataset_name": unique_name,
        "original_name": dataset_name,
        "dataset_description": dataset_description,
        "dataset_uri": dataset_uri,
        "old_version_id": old_version_id,
        "new_version_id": new_version_id,
        "old_version_file": old_file.filename,
        "new_version_file": new_file.filename,
    }

    try:
        dataset = adapter.dataset_description(dataset_name=unique_name)
        can_create = not bool(dataset)
    except EndPointNotFound:
        adapter.create_dataset(dataset_name=unique_name)
        can_create = True
        logger.info("creating dataset")

    if not can_create:
        logger.warning("dataset exists and is not empty, no diff created")
        raise HTTPException(HTTPStatus.CONFLICT, "Dataset is not empty.")

    try:
        with save_files(old_file, new_file, config.RDF_DIFFER_FILE_DB) as (
            db_location,
            saved_old,
            saved_new,
        ):
            task = async_create_diff.delay(
                unique_name, body, saved_old, saved_new, db_location, config.RDF_DIFFER_REPORTS_DB
            )
            push_task_to_queue(dumps([task.id, unique_name]))
            redis_client.set(task.id, str(False))
        logger.debug(f"task executed with id: {task.id}")
        return CreateDiffResponse(uid=task.id, dataset_name=unique_name)
    except ValueError as exception:
        text = "Internal error while uploading the diffs.\n" + str(exception)
        logger.exception(text)
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, text) from exception


@router.delete("/diffs/{dataset_id}")
def delete_diff(dataset_id: str = PathParam(...)) -> MessageResponse:
    """Delete a dataset and all its reports."""
    logger.debug(f"start delete dataset: {dataset_id} endpoint")
    try:
        _fuseki_adapter().delete_dataset(find_dataset_name_by_id(dataset_id))
        remove_all_reports(find_dataset_name_by_id(dataset_id), config.RDF_DIFFER_REPORTS_DB)
        logger.info(f"finish delete dataset: {dataset_id} endpoint")
        return MessageResponse(message=f"<{dataset_id}> deleted successfully.")
    except (FusekiException, FileNotFoundError) as exception:
        text = f"<{dataset_id}> does not exist."
        logger.exception(text)
        raise HTTPException(HTTPStatus.NOT_FOUND, text) from exception


@router.post("/diffs/report")
def build_report(body: ReportRequest) -> JSONResponse:
    """Generate a dataset diff report."""
    logger.debug(f"start build report for {body.dataset_id} endpoint")
    rebuild = strtobool(body.rebuild)
    dataset = get_diff(body.dataset_id)  # potential 404

    ap_manager = ApplicationProfileManager(
        application_profile=body.application_profile, template_type=body.template_type
    )
    try:
        template_location = ap_manager.get_template_folder()
        query_files = ap_manager.get_queries_dict()
    except (LookupError, FileNotFoundError) as exception:
        logger.exception(str(exception))
        raise HTTPException(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "Check valid application profiles and their template types through the API"
            "and if the queries folder exists in the chosen application profile folder",
        ) from exception

    name = find_dataset_name_by_id(body.dataset_id)
    if (
        report_exists(
            name, body.application_profile, body.template_type, config.RDF_DIFFER_REPORTS_DB
        )
        and not rebuild
    ):
        return JSONResponse(
            status_code=HTTPStatus.NOT_ACCEPTABLE,
            content=MessageResponse(
                message="Report already exists. To rebuild send the `rebuild` query parameter set to true"
            ).model_dump(),
        )

    task = async_generate_report.delay(
        dataset_name=name,
        application_profile=body.application_profile,
        template_type=body.template_type,
        db_location=config.RDF_DIFFER_REPORTS_DB,
        template_location=str(template_location),
        query_files=query_files,
        dataset=dataset,
    )
    return JSONResponse(
        content=ReportTaskResponse(
            task_id=task.id, application_profile=body.application_profile
        ).model_dump()
    )


@router.get("/diffs/report")
def get_report(
    dataset_id: str = Query(...),
    application_profile: str = Query(...),
    template_type: str = Query(...),
) -> FileResponse:
    """Download a previously built dataset diff report."""
    logger.debug(f"start get report for {dataset_id} endpoint")
    _ = get_diff(dataset_id)  # potential 404

    ap_manager = ApplicationProfileManager(
        application_profile=application_profile, template_type=template_type
    )
    try:
        _ = ap_manager.get_template_folder()
        _ = ap_manager.get_queries_dict()
    except (LookupError, FileNotFoundError) as exception:
        logger.exception(str(exception))
        raise HTTPException(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "Check valid application profiles and their template types through the API"
            "and if the queries folder exists in the chosen application profile folder",
        ) from exception

    name = find_dataset_name_by_id(dataset_id)
    if not report_exists(name, application_profile, template_type, config.RDF_DIFFER_REPORTS_DB):
        raise HTTPException(HTTPStatus.NOT_FOUND, "First send a request to build the report.")

    report_path = retrieve_report(
        name, application_profile, template_type, config.RDF_DIFFER_REPORTS_DB
    )
    return FileResponse(report_path, filename=Path(report_path).name)


# Declared after the static /diffs/report routes so FastAPI does not match
# "report" as a {dataset_id} (route matching is by declaration order).
@router.get("/diffs/{dataset_id}")
def get_diff(dataset_id: str = PathParam(...)) -> dict:
    """Get the dataset description."""
    logger.debug(f"get diff for {dataset_id} endpoint")
    try:
        meta = read_meta_file(
            build_dataset_reports_location(
                find_dataset_name_by_id(dataset_id), config.RDF_DIFFER_REPORTS_DB
            )
        )
    except Exception as exception:
        text = f"<{dataset_id}> does not exist."
        logger.exception(text)
        raise HTTPException(HTTPStatus.NOT_FOUND, text) from exception

    try:
        dataset = _fuseki_adapter().dataset_description(cast(str, meta.get("dataset_name")))
        dataset["available_reports"] = get_all_reports(
            cast(str, meta.get("dataset_name")), config.RDF_DIFFER_REPORTS_DB
        )
        return dataset
    except EndPointNotFound as exception:
        text = f"<{dataset_id}> does not exist."
        logger.exception(text)
        raise HTTPException(HTTPStatus.NOT_FOUND, text) from exception
    except (ValueError, IndexError) as exception:
        text = f"Unexpected Error. {str(exception)}"
        logger.exception(text)
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, text) from exception


@router.get("/aps")
def list_application_profiles() -> list:
    """List application profiles and their template variants."""
    return [
        {
            "application_profile": ap,
            "template_variations": ApplicationProfileManager(ap).list_template_variants(),
        }
        for ap in ApplicationProfileManager().list_aps()
    ]


@router.get("/tasks/active")
def list_active_tasks() -> list:
    """List active Celery tasks."""
    logger.debug("get active tasks")
    try:
        tasks = retrieve_active_tasks()
        active: list = tasks.get(list(tasks.keys())[0], [])
        return active
    except AttributeError:
        return []


@router.get("/tasks/{task_id}")
def get_task_status(task_id: str = PathParam(...)) -> dict:
    """Get the status of a task."""
    logger.debug(f"get task status: {task_id}")
    task = retrieve_task(task_id)
    if not task:
        raise HTTPException(HTTPStatus.NOT_FOUND, f"Task with {task_id} doesn't exist")
    try:
        result = dumps(task.result)
    except TypeError:
        result = ""
    return {"task_id": task.id, "status": task.status, "result": result}


@router.delete("/tasks/{task_id}")
def stop_task(task_id: str = PathParam(...)) -> MessageResponse:
    """Revoke a running task."""
    logger.debug(f"stop task: {task_id}")
    try:
        tasks = flatten_active_tasks(retrieve_active_tasks())
        task = next(task for task in tasks if task["id"] == task_id)
        kill_task(task, config.RDF_DIFFER_REPORTS_DB)
    except Exception as exception:
        raise HTTPException(
            HTTPStatus.NOT_ACCEPTABLE, "task already finished executing or does not exist"
        ) from exception
    return MessageResponse(message=f"task {task_id} set for revoking.")


def _as_file_storage(upload: UploadFile) -> FileStorage:
    """Adapt a FastAPI UploadFile to the werkzeug FileStorage that core adapters expect."""
    return FileStorage(
        stream=upload.file, filename=upload.filename, content_type=upload.content_type
    )
