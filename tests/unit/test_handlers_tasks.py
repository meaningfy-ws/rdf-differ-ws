from unittest.mock import MagicMock, patch

import pytest
from werkzeug.exceptions import NotAcceptable, NotFound

from rdf_differ.api.entrypoints.api.handlers import (
    get_active_tasks,
    get_application_profiles_details,
    get_task_status,
    stop_running_task,
)


@patch("rdf_differ.api.entrypoints.api.handlers.ApplicationProfileManager")
def test_get_application_profiles_details(mock_apm):
    instance = mock_apm.return_value
    instance.list_aps.return_value = ["ap1"]
    instance.list_template_variants.return_value = ["v1"]

    data, status = get_application_profiles_details()

    assert status == 200
    assert data == [{"application_profile": "ap1", "template_variations": ["v1"]}]


@patch("rdf_differ.api.entrypoints.api.handlers.retrieve_active_tasks")
def test_get_active_tasks_returns_first_workers_tasks(mock_active):
    mock_active.return_value = {"worker1": [{"id": "t1"}]}
    assert get_active_tasks() == ([{"id": "t1"}], 200)


@patch("rdf_differ.api.entrypoints.api.handlers.retrieve_active_tasks")
def test_get_active_tasks_handles_no_workers(mock_active):
    mock_active.return_value = None
    assert get_active_tasks() == ([], 200)


@patch("rdf_differ.api.entrypoints.api.handlers.retrieve_task")
def test_get_task_status_success(mock_retrieve):
    task = MagicMock(result={"k": "v"}, id="t1", status="SUCCESS")
    mock_retrieve.return_value = task

    data, status = get_task_status("t1")

    assert status == 200
    assert data["task_id"] == "t1"
    assert data["status"] == "SUCCESS"


@patch("rdf_differ.api.entrypoints.api.handlers.retrieve_task")
def test_get_task_status_unserialisable_result(mock_retrieve):
    mock_retrieve.return_value = MagicMock(result=object(), id="t1", status="STARTED")

    data, _ = get_task_status("t1")

    assert data["result"] == ""


@patch("rdf_differ.api.entrypoints.api.handlers.retrieve_task")
def test_get_task_status_not_found(mock_retrieve):
    mock_retrieve.return_value = None
    with pytest.raises(NotFound):
        get_task_status("missing")


@patch("rdf_differ.api.entrypoints.api.handlers.kill_task")
@patch("rdf_differ.api.entrypoints.api.handlers.flatten_active_tasks")
@patch("rdf_differ.api.entrypoints.api.handlers.retrieve_active_tasks")
def test_stop_running_task_success(mock_active, mock_flatten, mock_kill):
    mock_flatten.return_value = [{"id": "t1"}]

    data, status = stop_running_task("t1")

    assert status == 200
    mock_kill.assert_called_once()


@patch("rdf_differ.api.entrypoints.api.handlers.flatten_active_tasks")
@patch("rdf_differ.api.entrypoints.api.handlers.retrieve_active_tasks")
def test_stop_running_task_not_found_raises(mock_active, mock_flatten):
    mock_flatten.return_value = []
    with pytest.raises(NotAcceptable):
        stop_running_task("t1")
