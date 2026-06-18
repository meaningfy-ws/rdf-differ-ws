from unittest.mock import patch

import pytest

from rdf_differ.services.celery import CELERY_CREATE_DIFF, CELERY_GENERATE_REPORT
from rdf_differ.services.queue import (
    cleanup_diff_creation,
    cleanup_report_creation,
    kill_task,
    stop_task,
)


@patch("rdf_differ.services.queue.push_task_to_queue")
@patch("rdf_differ.services.queue.task_exists_in_queue")
def test_stop_task_queues_when_absent(mock_exists, mock_push):
    mock_exists.return_value = False
    stop_task("t1")
    mock_push.assert_called_once_with("t1")


@patch("rdf_differ.services.queue.task_exists_in_queue")
def test_stop_task_raises_when_already_queued(mock_exists):
    mock_exists.return_value = True
    with pytest.raises(ValueError, match="already marked for revoking"):
        stop_task("t1")


@patch("rdf_differ.services.queue.cleanup_diff_creation")
@patch("rdf_differ.services.queue.revoke_task")
def test_kill_task_for_create_diff(mock_revoke, mock_cleanup):
    kill_task({"id": "t1", "type": CELERY_CREATE_DIFF, "args": ["ds"]}, "db")
    mock_revoke.assert_called_once_with("t1", True)
    mock_cleanup.assert_called_once_with(dataset_id="ds")


@patch("rdf_differ.services.queue.cleanup_report_creation")
@patch("rdf_differ.services.queue.revoke_task")
def test_kill_task_for_generate_report(mock_revoke, mock_cleanup):
    kill_task({"id": "t1", "type": CELERY_GENERATE_REPORT, "args": ["ds", "ap", "tt"]}, "db")
    mock_revoke.assert_called_once_with("t1", True)
    mock_cleanup.assert_called_once_with("ds", "ap", "tt", "db")


@patch("rdf_differ.services.queue.remove_report")
def test_cleanup_report_creation_delegates(mock_remove):
    cleanup_report_creation("ds", "ap", "tt", "db")
    mock_remove.assert_called_once_with("ds", "ap", "tt", "db")


@patch("rdf_differ.services.queue.FusekiDiffAdapter")
def test_cleanup_diff_creation_deletes_dataset(mock_adapter):
    cleanup_diff_creation("ds")
    mock_adapter.return_value.delete_dataset.assert_called_once_with("ds")
