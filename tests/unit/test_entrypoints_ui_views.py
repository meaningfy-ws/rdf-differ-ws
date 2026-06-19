#!/usr/bin/python3

# test_entrypoints_ui_views.py
# Date:  18/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from io import BytesIO
from json import dumps
from unittest.mock import patch

from bs4 import BeautifulSoup
from werkzeug.datastructures import FileStorage


@patch("rdf_differ.api.entrypoints.ui.views.get_datasets")
def test_index(mock_get_datasets, ui_client):
    mock_get_datasets.return_value = (
        [
            {
                "uid": "uid_one",
                "original_name": "dataset_one",
            },
            {
                "uid": "uid_two",
                "original_name": "dataset_two",
            },
        ],
        200,
    )

    response = ui_client.get("/")
    soup = BeautifulSoup(response.data, "html.parser")

    title = soup.find("h1")
    assert "List of calculated diffs" in title.get_text()

    table_body = soup.find("tbody")
    rows = table_body.find_all("tr")
    assert len(rows) == 2
    assert "dataset_one" in rows[0].get_text()
    assert "dataset_two" in rows[1].get_text()


@patch("rdf_differ.api.entrypoints.ui.views.api_create_diff")
def test_create_diff_failure_dataset_is_not_empty(mock_create_diff, ui_client):
    mock_create_diff.return_value = (
        dumps(
            {
                "detail": "Dataset is not empty.",
                "status": 409,
                "title": "Conflict",
                "type": "about:blank",
            }
        ),
        409,
    )

    data = {
        "dataset_name": "dataset_name",
        "dataset_description": "dataset description",
        "dataset_uri": "http://dataset.uri",
        "old_version_file_content": FileStorage(BytesIO(b"old content"), "old.rdf"),
        "new_version_file_content": FileStorage(BytesIO(b"new content"), "new.rdf"),
        "old_version_id": "old_version_id",
        "new_version_id": "new_version_id",
    }

    response = ui_client.post(
        "/create-diff", data=data, follow_redirects=True, content_type="multipart/form-data"
    )

    soup = BeautifulSoup(response.data, "html.parser")
    body = soup.get_text()

    assert "Status: 409. Title: Conflict Detail: Dataset is not empty." in body


@patch("rdf_differ.api.entrypoints.ui.views.api_create_diff")
def test_create_diff_incorrect_dataset_name(mock_create_diff, ui_client):
    mock_create_diff.return_value = {}, 200

    data = {
        "dataset_name": "dataset name",
        "dataset_description": "dataset description",
        "dataset_uri": "http://dataset.uri",
        "old_version_file_content": FileStorage(BytesIO(b"old content"), "old.rdf"),
        "new_version_file_content": FileStorage(BytesIO(b"new content"), "new.rdf"),
        "old_version_id": "old_version_id",
        "new_version_id": "new_version_id",
    }

    response = ui_client.post(
        "/create-diff", data=data, follow_redirects=True, content_type="multipart/form-data"
    )

    soup = BeautifulSoup(response.data, "html.parser")
    body = soup.get_text()

    assert "Dataset name can contain only letters, numbers, _, :, and -" in body

    data["dataset_name"] = "&3fldsaj//"
    data["old_version_file_content"] = FileStorage(BytesIO(b"old content"), "old.rdf")
    data["new_version_file_content"] = FileStorage(BytesIO(b"new content"), "new.rdf")

    response = ui_client.post(
        "/create-diff", data=data, follow_redirects=True, content_type="multipart/form-data"
    )

    soup = BeautifulSoup(response.data, "html.parser")
    body = soup.get_text()

    assert "Dataset name can contain only letters, numbers, _, :, and -" in body


@patch("rdf_differ.api.entrypoints.ui.views.get_report")
def test_download_report_success(mock_get_report, ui_client):
    dataset_id = "dataset"
    application_profile = "ap"
    template_type = "type"
    mock_get_report.return_value = b"important report", ".html", 200

    response = ui_client.get(f"/diff-report/{dataset_id}/{application_profile}/{template_type}")
    assert "important report" in response.data.decode()


@patch("rdf_differ.api.entrypoints.ui.views.get_datasets")
@patch("rdf_differ.api.entrypoints.ui.views.get_report")
def test_download_report_failure(mock_get_report, mock_get_datasets, ui_client):
    dataset_id = "dataset"
    application_profile = "ap"
    template_type = "type"
    mock_get_report.side_effect = Exception("report error")
    mock_get_datasets.return_value = [], 200

    response = ui_client.get(f"/diff-report/{dataset_id}/{application_profile}/{template_type}")
    soup = BeautifulSoup(response.data, "html.parser")

    # check if redirected to index page
    title = soup.find("h1")
    assert "List of calculated diffs" in title.get_text()

    # check if error is displayed
    error = soup.find("div", {"class": "card red lighten-3"})
    assert "report error" in error.get_text()
