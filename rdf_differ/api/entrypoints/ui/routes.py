"""Web UI page routes (EPIC api-ui-fastapi-modernization, DEC-2).

Server-rendered pages on FastAPI + Jinja2. Each route calls the REST API through the
httpx ``api_client`` and renders a template or redirects; API failures become flash
messages, never a UI crash (DEC-3).
"""

import logging
import re

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from pydantic import ValidationError

from rdf_differ import config
from rdf_differ.api.entrypoints.ui import api_client
from rdf_differ.api.entrypoints.ui.forms import CreateDiffInput
from rdf_differ.api.entrypoints.ui.rendering import flash, render
from rdf_differ.api.entrypoints.ui.security import validate_csrf

logger = logging.getLogger(config.RDF_DIFFER_LOGGER)
router = APIRouter()

_SEE_OTHER = 303


@router.get("/", name="index")
def index(request: Request) -> Response:
    result = api_client.get_datasets()
    if not result.ok:
        flash(request, result.error_message(), "error")
    datasets = result.json if result.ok and isinstance(result.json, list) else []
    return render(request, "index.html", datasets=datasets, active_page="index")


@router.get("/create-diff", name="create_diff")
def create_diff_form(request: Request) -> Response:
    defaults = {"old_version_id": "old", "new_version_id": "new"}
    return render(
        request, "dataset/create_diff.html", active_page="create_diff", form=defaults, errors={}
    )


@router.post("/create-diff")
async def create_diff_submit(
    request: Request,
    dataset_name: str = Form(""),
    dataset_uri: str = Form(""),
    old_version_id: str = Form("old"),
    new_version_id: str = Form("new"),
    dataset_description: str = Form(""),
    csrf_token: str = Form(""),
    old_version_file_content: UploadFile | None = File(None),
    new_version_file_content: UploadFile | None = File(None),
) -> Response:
    validate_csrf(request, csrf_token)
    submitted = {
        "dataset_name": dataset_name,
        "dataset_uri": dataset_uri,
        "old_version_id": old_version_id,
        "new_version_id": new_version_id,
        "dataset_description": dataset_description,
    }
    errors: dict[str, str] = {}
    try:
        valid = CreateDiffInput(**submitted)
    except ValidationError as exception:
        errors = {str(error["loc"][0]): error["msg"] for error in exception.errors()}

    for field, upload in (
        ("old_version_file_content", old_version_file_content),
        ("new_version_file_content", new_version_file_content),
    ):
        if upload is None or not upload.filename:
            errors[field] = "A file is required"

    if errors:
        return render(
            request,
            "dataset/create_diff.html",
            active_page="create_diff",
            form=submitted,
            errors=errors,
        )

    # Both uploads are present here — the loop above recorded an error otherwise.
    assert old_version_file_content is not None
    assert new_version_file_content is not None
    files = {
        "old_version_file_content": (
            old_version_file_content.filename,
            await old_version_file_content.read(),
            old_version_file_content.content_type,
        ),
        "new_version_file_content": (
            new_version_file_content.filename,
            await new_version_file_content.read(),
            new_version_file_content.content_type,
        ),
    }
    result = api_client.create_diff(data=valid.model_dump(), files=files)
    if result.ok:
        flash(request, "Diff creation started.", "success")
        return RedirectResponse(request.url_for("get_active_tasks"), status_code=_SEE_OTHER)

    flash(request, result.error_message(), "error")
    return render(
        request, "dataset/create_diff.html", active_page="create_diff", form=submitted, errors={}
    )


@router.get("/diffs/{dataset_id}", name="view_dataset")
def view_dataset(request: Request, dataset_id: str) -> Response:
    dataset_result = api_client.get_dataset(dataset_id)
    if not dataset_result.ok:
        flash(request, dataset_result.error_message(), "error")
        return RedirectResponse(request.url_for("index"), status_code=_SEE_OTHER)

    profiles_result = api_client.get_application_profiles()
    profiles = profiles_result.json if profiles_result.ok else []
    return render(
        request,
        "dataset/view_dataset.html",
        active_page="view_dataset",
        dataset=dataset_result.json,
        application_profiles=profiles,
    )


@router.post("/diffs/{dataset_id}")
def build_report(
    request: Request,
    dataset_id: str,
    application_profile: str = Form(...),
    template_type: str = Form(...),
    csrf_token: str = Form(""),
) -> Response:
    validate_csrf(request, csrf_token)
    result = api_client.build_report(dataset_id, application_profile, template_type)
    if result.ok:
        flash(request, "Report building started.", "success")
    else:
        flash(request, result.error_message(), "error")
    return RedirectResponse(
        request.url_for("view_dataset", dataset_id=dataset_id), status_code=_SEE_OTHER
    )


@router.get(
    "/diff-report/{dataset_id}/{application_profile}/{template_type}", name="download_report"
)
def download_report(
    request: Request, dataset_id: str, application_profile: str, template_type: str
) -> Response:
    response = api_client.get_report(dataset_id, application_profile, template_type)
    if response.status_code != 200:
        flash(request, "Could not download the report. Build it first.", "error")
        return RedirectResponse(request.url_for("index"), status_code=_SEE_OTHER)

    disposition = response.headers.get("content-disposition", "")
    match = re.search(r'filename="?([^"]+)"?', disposition)
    extension = match.group(1).split(".")[-1] if match and "." in match.group(1) else "html"
    filename = f"report-{dataset_id}-{application_profile}-{template_type}.{extension}"
    return Response(
        content=response.content,
        media_type=response.headers.get("content-type", "application/octet-stream"),
        headers={"content-disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/tasks", name="get_active_tasks")
def get_active_tasks(request: Request) -> Response:
    result = api_client.get_active_tasks()
    if not result.ok:
        flash(request, result.error_message(), "error")
    tasks = result.json if result.ok and isinstance(result.json, list) else []
    return render(
        request, "tasks/view_active_tasks.html", tasks=tasks, active_page="view_active_tasks"
    )


@router.post("/revoke-task/{task_id}", name="revoke_task")
def revoke_task(request: Request, task_id: str, csrf_token: str = Form("")) -> Response:
    validate_csrf(request, csrf_token)
    result = api_client.revoke_task(task_id)
    category = "success" if result.ok else "error"
    message = (
        result.json.get("message") if isinstance(result.json, dict) else result.error_message()
    )
    flash(request, message or "Task revoke requested.", category)
    return RedirectResponse(request.url_for("get_active_tasks"), status_code=_SEE_OTHER)
