#!/usr/bin/python3

# conftest.py
# Date: 20/07/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com


from io import BytesIO

from werkzeug.datastructures import FileStorage


def helper_create_diff(file_1=None, file_2=None, body=None):
    file_1 = file_1 if file_1 else FileStorage((BytesIO(b'1')), filename='old_file.rdf')
    file_2 = file_2 if file_2 else FileStorage((BytesIO(b'2')), filename='new_file.rdf')
    body = body if body else {
        'dataset_id': 'dataset',
        'dataset_uri': 'uri',
        'old_version_id': 'old',
        'new_version_id': 'new',
    }
    return file_1, file_2, body
