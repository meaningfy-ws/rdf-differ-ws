"""
diffs.py
Date: 30/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from rdf_differ.diff_adapter import FusekiDiffAdapter


def get_diffs():
    """
    List the existent datasets.

    :return: list of datasets
    """
    fuseki_adapter = FusekiDiffAdapter('http://localhost:3030')
    datasets = fuseki_adapter.list_datasets()
    return [{dataset: fuseki_adapter.diff_description(dataset)} for dataset in datasets]


def create_diff(dataset_id, dataset_uri, new_version_id, old_version_id, new_version_file_content,
                new_version_file_name, old_version_file_content, old_version_file_name):
    """

    :param dataset_id:http://localhost:3030/subdiv/sparql
    :param dataset_uri:
    :param new_version_id:
    :param old_version_id:
    :param new_version_file_content:
    :param new_version_file_name:
    :param old_version_file_content:
    :param old_version_file_name:
    :return:
    """


def get_diff(dataset_id):
    """

    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    :return:
    """
    return FusekiDiffAdapter('http://localhost:3030').diff_description(dataset_id)


def delete_diff(dataset_id):
    """

    :param dataset_id:
    :return:
    """
