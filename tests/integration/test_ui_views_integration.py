#!/usr/bin/python3

# UI view tests that exercise the UI -> API HTTP integration.
# These mock the directly-called ui.views functions but still reach the running API for
# secondary calls (application profiles `/aps`, active tasks `/tasks/active`), so they need
# a live API service on RDF_DIFFER_API_PORT (e.g. `make start-services-test`). The marker
# is applied by path (tests/integration/ -> `integration`) via tests/conftest.py.
from io import BytesIO
from unittest.mock import patch

from bs4 import BeautifulSoup
from werkzeug.datastructures import FileStorage


@patch("rdf_differ.api.entrypoints.ui.views.get_dataset")
def test_get_dataset(mock_get_dataset, ui_client):
    dataset_id = "uid"
    dataset_name = "dataset_one123456"
    original_name = "dataset_one"
    dataset_description = "dataset_one is a dataset"
    mock_get_dataset.return_value = (
        {
            "dataset_name": f"{dataset_name}",
            "original_name": f"{original_name}",
            "dataset_description": f"{dataset_description}",
            "dataset_uri": "http://dataset.one",
            "old_version_file": "one_old.ttl",
            "new_version_file": "one_new.ttl",
            "dataset_versions": ["one_old", "one_new"],
            "version_named_graphs": ["http://one.version/one_old", "http://one.version/one_new"],
            "diff_date": "2020",
        },
        200,
    )

    response = ui_client.get(f"/diffs/{dataset_id}")
    soup = BeautifulSoup(response.data, "html.parser")

    title = soup.find("h1")
    assert "dataset_one" in title.get_text()

    table_body = soup.find("tbody")
    rows = table_body.find_all("tr")
    assert len(rows) == 8
    assert "dataset_one123456" in rows[0].get_text()
    assert "dataset_one is a dataset" in rows[1].get_text()
    assert "dataset.one" in rows[2].get_text()
    assert "one_old" in rows[3].get_text()
    assert "one_new" in rows[3].get_text()
    assert "one.version/one_old" in rows[5].get_text()
    assert "one.version/one_new" in rows[5].get_text()
    assert "one_old.ttl" in rows[6].get_text()
    assert "one_new.ttl" in rows[7].get_text()


@patch("rdf_differ.api.entrypoints.ui.views.get_dataset")
@patch("rdf_differ.api.entrypoints.ui.views.api_create_diff")
def test_create_diff_success(mock_create_diff, mock_get_dataset, ui_client):
    mock_create_diff.return_value = {}, 200
    # required data for the redirect after successful submission
    mock_get_dataset.return_value = (
        {
            "dataset_id": "/dataset_name",
            "dataset_uri": "http://dataset.uri",
            "new_version_id": "new_version_id",
            "old_version_id": "old_version_id",
            "dataset_versions": ["old_version_id", "new_version_id"],
            "version_named_graphs": ["http://one.version/one_old", "http://one.version/one_new"],
            "diff_date": "2020",
        },
        200,
    )

    response = ui_client.get("/create-diff")
    soup = BeautifulSoup(response.data, "html.parser")

    title = soup.find("h1")
    assert "Create a dataset" in title.get_text()

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
    title = soup.find("h1")

    assert response.status_code == 200
    assert "List of active tasks" in title.get_text()
