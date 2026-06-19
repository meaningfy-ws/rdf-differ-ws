from io import BytesIO
from unittest.mock import patch

from werkzeug.datastructures import FileStorage

from rdf_differ.api.entrypoints.ui import api_wrapper


@patch("rdf_differ.api.entrypoints.ui.api_wrapper.requests")
def test_get_datasets(mock_requests):
    mock_requests.get.return_value.json.return_value = [{"uid": "1"}]
    mock_requests.get.return_value.status_code = 200
    assert api_wrapper.get_datasets() == ([{"uid": "1"}], 200)


@patch("rdf_differ.api.entrypoints.ui.api_wrapper.requests")
def test_get_dataset(mock_requests):
    mock_requests.get.return_value.json.return_value = {"dataset_name": "ds"}
    mock_requests.get.return_value.status_code = 200
    assert api_wrapper.get_dataset("uid") == ({"dataset_name": "ds"}, 200)


@patch("rdf_differ.api.entrypoints.ui.api_wrapper.requests")
def test_get_application_profiles(mock_requests):
    mock_requests.get.return_value.json.return_value = ["ap1"]
    mock_requests.get.return_value.status_code = 200
    assert api_wrapper.get_application_profiles() == (["ap1"], 200)


@patch("rdf_differ.api.entrypoints.ui.api_wrapper.requests")
def test_get_active_tasks(mock_requests):
    mock_requests.get.return_value.json.return_value = []
    mock_requests.get.return_value.status_code = 200
    assert api_wrapper.get_active_tasks() == ([], 200)


@patch("rdf_differ.api.entrypoints.ui.api_wrapper.requests")
def test_revoke_task(mock_requests):
    mock_requests.delete.return_value.json.return_value = {"message": "ok"}
    mock_requests.delete.return_value.status_code = 200
    assert api_wrapper.revoke_task("t1") == ({"message": "ok"}, 200)


@patch("rdf_differ.api.entrypoints.ui.api_wrapper.requests")
def test_build_report(mock_requests):
    mock_requests.post.return_value.text = "queued"
    mock_requests.post.return_value.status_code = 200
    assert api_wrapper.build_report("ds", "ap", "tt") == ("queued", 200)


@patch("rdf_differ.api.entrypoints.ui.api_wrapper.requests")
def test_get_report_parses_filename_extension(mock_requests):
    mock_requests.get.return_value.headers = {
        "content-disposition": "attachment; filename=report.html"
    }
    mock_requests.get.return_value.content = b"<html></html>"
    mock_requests.get.return_value.status_code = 200
    content, extension, status = api_wrapper.get_report("ds", "ap", "tt")
    assert content == b"<html></html>"
    assert extension == ".html"
    assert status == 200


@patch("rdf_differ.api.entrypoints.ui.api_wrapper.requests")
def test_create_diff_posts_files_and_data(mock_requests):
    mock_requests.post.return_value.text = "created"
    mock_requests.post.return_value.status_code = 200
    old_file = FileStorage(BytesIO(b"old"), "old.rdf")
    new_file = FileStorage(BytesIO(b"new"), "new.rdf")

    result = api_wrapper.create_diff("ds", "desc", "http://uri", "v1", old_file, "v2", new_file)

    assert result == ("created", 200)
    _, kwargs = mock_requests.post.call_args
    assert "old_version_file_content" in kwargs["files"]
    assert kwargs["data"]["dataset_name"] == "ds"
