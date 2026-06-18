from unittest.mock import MagicMock, patch

from rdf_differ.services.tasks import (
    flatten_active_tasks,
    retrieve_active_tasks,
    retrieve_task,
    revoke_task,
)


def test_flatten_active_tasks_returns_first_workers_list():
    assert flatten_active_tasks({"worker1": [{"id": "a"}, {"id": "b"}]}) == [
        {"id": "a"},
        {"id": "b"},
    ]


def test_retrieve_active_tasks_uses_the_worker_inspector():
    worker = MagicMock()
    worker.control.inspect.return_value.active.return_value = {"worker1": []}
    assert retrieve_active_tasks(worker=worker) == {"worker1": []}


def test_revoke_task_calls_control_revoke():
    worker = MagicMock()
    revoke_task("t1", terminate=True, worker=worker)
    worker.control.revoke.assert_called_once_with("t1", terminate=True)


@patch("rdf_differ.services.tasks.AsyncResult")
def test_retrieve_task_builds_async_result(mock_async_result):
    worker = MagicMock()
    retrieve_task("t1", worker=worker)
    mock_async_result.assert_called_once_with("t1", app=worker)
