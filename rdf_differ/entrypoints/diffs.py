"""
diffs.py
Date: 30/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from rdf_differ.diff_adapter import FusekiDiffAdapter


def get_diffs() -> tuple:
    """
        List the existent datasets with their descriptions.
    :return: list of existent datasets
    :rtype: list, int
    """
    fuseki_adapter = FusekiDiffAdapter('http://localhost:3030')
    datasets, status = fuseki_adapter.list_datasets()
    return [{dataset: fuseki_adapter.diff_description(dataset)[0]} for dataset in datasets], status


def create_diff(dataset_id, dataset_uri, new_version_id, old_version_id, new_version_file_content,
                new_version_file_name, old_version_file_content, old_version_file_name) -> tuple:
    """

    :param dataset_id:
    :param dataset_uri:
    :param new_version_id:
    :param old_version_id:
    :param new_version_file_content:
    :param new_version_file_name:
    :param old_version_file_content:
    :param old_version_file_name:
    :return: created diff description
    :rtype: dict, int
    """
    return {}, 200


def get_diff(dataset_id) -> tuple:
    """
        Get the dataset description
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :return: dataset description
    :rtype: dict, int
    """
    return FusekiDiffAdapter('http://localhost:3030').diff_description(dataset_id)


def delete_diff(dataset_id) -> tuple:
    """
        Delete a dataset
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :return: info about deletion
    :rtype: text, int
    """
    return FusekiDiffAdapter('http://localhost:3030').delete_dataset(dataset_id)
