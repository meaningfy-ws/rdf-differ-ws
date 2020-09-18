#!/usr/bin/python3

# api.py
# Date:  18/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Service to consume API

"""
import requests

from rdf_differ.entrypoints.ui import config


def get_datasets():
    datasets = requests.get(config.API_ENDPOINT + '/diffs')
    return datasets.json()


def get_dataset(dataset_id):
    return requests.get(config.API_ENDPOINT + '/diffs/' + dataset_id).json()


def create_diff(dataset_name, dataset_description, dataset_uri,
                old_version_id, old_version_file, new_version_id, new_version_file):
    files = {
        'old_version_file_content': (old_version_file.filename, old_version_file.stream, old_version_file.mimetype),
        'new_version_file_content': (new_version_file.filename, new_version_file.stream, new_version_file.mimetype),
    }
    data = {
        'dataset_id': dataset_name,
        'dataset_description': dataset_description,
        'dataset_uri': dataset_uri,
        'old_version_id': old_version_id,
        'new_version_id': new_version_id
    }
    response = requests.post(config.API_ENDPOINT + '/diffs', data=data, files=files)
    return response.text
