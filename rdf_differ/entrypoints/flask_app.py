"""
flask_app.py
Date:  28/07/2020
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com 
"""

import connexion
import datetime
import logging
from rdf_differ import config

app = connexion.FlaskApp(__name__, specification_dir='openapi')
app.add_api('openapi.yaml')
app.run(port=config.RDF_DIFFER_API_PORT)


def get_diffs():
    """

    :return:
    """


def create_diff(dataset_id, dataset_uri, new_version_id, old_version_id, new_version_file_content,
                new_version_file_name, old_version_file_content, old_version_file_name):
    """

    :param dataset_id:
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

    :param dataset_id:
    :return:
    """


def delete_diff(dataset_id):
    """

    :param dataset_id:
    :return:
    """
