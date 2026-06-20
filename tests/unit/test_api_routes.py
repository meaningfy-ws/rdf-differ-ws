"""Unit tests for the FastAPI REST API routes (EPIC api-ui-fastapi-modernization).

Exercised through FastAPI's TestClient with the services/adapters mocked — the routes'
job is request parsing, calling a service, mapping errors and serialising a response.
Replaces the former Connexion handler tests.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from SPARQLWrapper.SPARQLExceptions import EndPointNotFound

from rdf_differ.api.entrypoints.api.app import app
from rdf_differ.diffing.adapters.diff_adapter import FusekiDiffAdapter
from rdf_differ.diffing.adapters.exceptions import FusekiException
from rdf_differ.reporting.services.ap_manager import ApplicationProfileManager

ROUTES = "rdf_differ.api.entrypoints.api.routes"

client = TestClient(app)


@contextmanager
def _fake_save_files(*_args, **_kwargs):
    yield ("/db/loc", "old.rdf", "new.rdf")


def _raise_404(*_args, **_kwargs):
    from fastapi import HTTPException

    raise HTTPException(404, "<dataset> does not exist.")


def _files():
    return {
        "old_version_file_content": ("old.rdf", b"<a> <b> <c> .", "application/rdf+xml"),
        "new_version_file_content": ("new.rdf", b"<a> <b> <d> .", "application/rdf+xml"),
    }


def _create_form():
    return {
        "dataset_name": "dataset",
        "dataset_uri": "uri",
        "old_version_id": "old",
        "new_version_id": "new",
    }


# --- GET /diffs -----------------------------------------------------------------


@patch.object(FusekiDiffAdapter, "dataset_description")
@patch.object(FusekiDiffAdapter, "list_datasets")
def test_list_diffs_200(mock_list, mock_desc):
    mock_list.return_value = ["a", "b"]
    mock_desc.side_effect = [{"dataset_id": "a"}, {"dataset_id": "b"}]

    resp = client.get("/diffs")

    assert resp.status_code == 200
    assert {d["dataset_id"] for d in resp.json()} == {"a", "b"}


@patch.object(FusekiDiffAdapter, "list_datasets")
def test_list_diffs_500(mock_list):
    mock_list.side_effect = FusekiException("boom")

    resp = client.get("/diffs")

    assert resp.status_code == 500
    assert "boom" in resp.json()["detail"]


# --- GET /diffs/{id} ------------------------------------------------------------


@patch(f"{ROUTES}.get_all_reports", return_value=[])
@patch(f"{ROUTES}.read_meta_file", return_value={"uid": "1", "dataset_name": "dataset"})
@patch(f"{ROUTES}.build_dataset_reports_location")
@patch(f"{ROUTES}.find_dataset_name_by_id", return_value="dataset")
@patch.object(FusekiDiffAdapter, "dataset_description", return_value={"dataset_name": "dataset"})
def test_get_diff_200(mock_desc, mock_find, mock_loc, mock_meta, mock_reports):
    resp = client.get("/diffs/dataset")

    assert resp.status_code == 200
    assert resp.json() == {"dataset_name": "dataset", "available_reports": []}


@patch(f"{ROUTES}.read_meta_file", return_value={"dataset_name": "dataset"})
@patch(f"{ROUTES}.build_dataset_reports_location")
@patch(f"{ROUTES}.find_dataset_name_by_id", return_value="dataset")
@patch.object(FusekiDiffAdapter, "dataset_description", side_effect=EndPointNotFound)
def test_get_diff_404(mock_desc, mock_find, mock_loc, mock_meta):
    resp = client.get("/diffs/dataset")

    assert resp.status_code == 404
    assert "<dataset> does not exist." in resp.json()["detail"]


# --- POST /diffs ----------------------------------------------------------------


@patch(f"{ROUTES}.redis_client")
@patch(f"{ROUTES}.push_task_to_queue")
@patch(f"{ROUTES}.async_create_diff")
@patch.object(FusekiDiffAdapter, "dataset_description", return_value={})
def test_create_diff_200(mock_desc, mock_async, mock_push, mock_redis):
    mock_async.delay.return_value = MagicMock(id="task-123")
    with patch(f"{ROUTES}.save_files", _fake_save_files):
        resp = client.post("/diffs", data=_create_form(), files=_files())

    assert resp.status_code == 200
    assert resp.json() == {"uid": "task-123", "dataset_name": resp.json()["dataset_name"]}
    assert resp.json()["uid"] == "task-123"


@patch.object(FusekiDiffAdapter, "create_dataset")
@patch(f"{ROUTES}.redis_client")
@patch(f"{ROUTES}.push_task_to_queue")
@patch(f"{ROUTES}.async_create_diff")
@patch.object(FusekiDiffAdapter, "dataset_description", side_effect=EndPointNotFound)
def test_create_diff_200_when_dataset_absent(
    mock_desc, mock_async, mock_push, mock_redis, mock_create
):
    mock_async.delay.return_value = MagicMock(id="task-9")
    with patch(f"{ROUTES}.save_files", _fake_save_files):
        resp = client.post("/diffs", data=_create_form(), files=_files())

    assert resp.status_code == 200
    mock_create.assert_called_once()


@patch.object(FusekiDiffAdapter, "dataset_description", return_value={"dataset_uri": "x"})
def test_create_diff_409_not_empty(mock_desc):
    resp = client.post("/diffs", data=_create_form(), files=_files())

    assert resp.status_code == 409
    assert "not empty" in resp.json()["detail"]


def test_create_diff_409_bad_name():
    form = _create_form() | {"dataset_name": "bad name!"}
    resp = client.post("/diffs", data=form, files=_files())

    assert resp.status_code == 409


def test_create_diff_422_missing_file():
    resp = client.post("/diffs", data=_create_form())  # no files

    assert resp.status_code == 422


# --- DELETE /diffs/{id} ---------------------------------------------------------


@patch(f"{ROUTES}.remove_all_reports")
@patch(f"{ROUTES}.find_dataset_name_by_id", return_value="dataset")
@patch.object(FusekiDiffAdapter, "delete_dataset")
def test_delete_diff_200(mock_delete, mock_find, mock_remove):
    resp = client.delete("/diffs/dataset")

    assert resp.status_code == 200
    assert "deleted successfully" in resp.json()["message"]


@patch(f"{ROUTES}.find_dataset_name_by_id", return_value="dataset")
@patch.object(FusekiDiffAdapter, "delete_dataset", side_effect=FusekiException)
def test_delete_diff_404(mock_delete, mock_find):
    resp = client.delete("/diffs/dataset")

    assert resp.status_code == 404


# --- POST /diffs/report ---------------------------------------------------------


def _report_body():
    return {"dataset_id": "dataset", "application_profile": "ap", "template_type": "tt"}


@patch(f"{ROUTES}.async_generate_report")
@patch(f"{ROUTES}.report_exists", return_value=False)
@patch(f"{ROUTES}.find_dataset_name_by_id", return_value="dataset")
@patch.object(ApplicationProfileManager, "get_queries_dict", return_value={})
@patch.object(ApplicationProfileManager, "get_template_folder", return_value="/tmp/x")
@patch(f"{ROUTES}.get_diff", return_value={})
def test_build_report_200(mock_diff, mock_tf, mock_q, mock_find, mock_exists, mock_async):
    mock_async.delay.return_value = MagicMock(id="t1")

    resp = client.post("/diffs/report", json=_report_body())

    assert resp.status_code == 200
    assert resp.json()["task_id"] == "t1"


@patch(f"{ROUTES}.report_exists", return_value=True)
@patch(f"{ROUTES}.find_dataset_name_by_id", return_value="dataset")
@patch.object(ApplicationProfileManager, "get_queries_dict", return_value={})
@patch.object(ApplicationProfileManager, "get_template_folder", return_value="/tmp/x")
@patch(f"{ROUTES}.get_diff", return_value={})
def test_build_report_406_exists(mock_diff, mock_tf, mock_q, mock_find, mock_exists):
    resp = client.post("/diffs/report", json=_report_body())

    assert resp.status_code == 406
    assert "already exists" in resp.json()["message"]


@patch.object(ApplicationProfileManager, "get_template_folder", side_effect=LookupError)
@patch(f"{ROUTES}.get_diff", return_value={})
def test_build_report_422(mock_diff, mock_tf):
    resp = client.post("/diffs/report", json=_report_body())

    assert resp.status_code == 422


@patch(f"{ROUTES}.get_diff", side_effect=_raise_404)
def test_build_report_404(mock_diff):
    resp = client.post("/diffs/report", json=_report_body())

    assert resp.status_code == 404


# --- GET /diffs/report ----------------------------------------------------------


@patch(f"{ROUTES}.report_exists", return_value=False)
@patch(f"{ROUTES}.find_dataset_name_by_id", return_value="dataset")
@patch.object(ApplicationProfileManager, "get_queries_dict", return_value={})
@patch.object(ApplicationProfileManager, "get_template_folder", return_value="/tmp/x")
@patch(f"{ROUTES}.get_diff", return_value={})
def test_get_report_404(mock_diff, mock_tf, mock_q, mock_find, mock_exists):
    resp = client.get(
        "/diffs/report",
        params={"dataset_id": "d", "application_profile": "ap", "template_type": "tt"},
    )

    assert resp.status_code == 404


def test_get_report_422_missing_params():
    resp = client.get("/diffs/report", params={"dataset_id": "d"})

    assert resp.status_code == 422


# --- GET /aps -------------------------------------------------------------------


@patch.object(ApplicationProfileManager, "list_template_variants", return_value=["html"])
@patch.object(ApplicationProfileManager, "list_aps", return_value=["ap1", "ap2"])
def test_list_application_profiles_200(mock_aps, mock_variants):
    resp = client.get("/aps")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["application_profile"] == "ap1"
    assert body[0]["template_variations"] == ["html"]


# --- tasks endpoints ------------------------------------------------------------


@patch(f"{ROUTES}.retrieve_active_tasks", return_value={"worker1": [{"id": "t1"}, {"id": "t2"}]})
def test_list_active_tasks_200(mock_active):
    resp = client.get("/tasks/active")

    assert resp.status_code == 200
    assert resp.json() == [{"id": "t1"}, {"id": "t2"}]


@patch(f"{ROUTES}.retrieve_active_tasks", side_effect=AttributeError)
def test_list_active_tasks_empty(mock_active):
    resp = client.get("/tasks/active")

    assert resp.status_code == 200
    assert resp.json() == []


@patch(f"{ROUTES}.retrieve_task")
def test_get_task_status_200(mock_retrieve):
    mock_retrieve.return_value = MagicMock(id="t1", status="SUCCESS", result={"ok": True})

    resp = client.get("/tasks/t1")

    assert resp.status_code == 200
    assert resp.json()["task_id"] == "t1"
    assert resp.json()["status"] == "SUCCESS"


@patch(f"{ROUTES}.retrieve_task", return_value=None)
def test_get_task_status_404(mock_retrieve):
    resp = client.get("/tasks/missing")

    assert resp.status_code == 404


@patch(f"{ROUTES}.kill_task")
@patch(f"{ROUTES}.flatten_active_tasks", return_value=[{"id": "t1"}])
@patch(f"{ROUTES}.retrieve_active_tasks", return_value={})
def test_stop_task_200(mock_active, mock_flatten, mock_kill):
    resp = client.delete("/tasks/t1")

    assert resp.status_code == 200
    assert "set for revoking" in resp.json()["message"]


@patch(f"{ROUTES}.flatten_active_tasks", return_value=[])
@patch(f"{ROUTES}.retrieve_active_tasks", return_value={})
def test_stop_task_406(mock_active, mock_flatten):
    resp = client.delete("/tasks/missing")

    assert resp.status_code == 406


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
