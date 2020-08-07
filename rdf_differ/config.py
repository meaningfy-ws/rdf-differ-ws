"""
config.py
Date: 20/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
import os
from typing import Union


def get_envs(key: str = None) -> Union[str, dict]:
    envs = {
        'filename': os.environ.get('FILENAME', 'file'),
        'endpoint': os.environ.get('ENDPOINT', 'http://localhost:3030')
    }

    if key:
        return envs.get(key)

    return envs


RDF_DIFFER_API_PORT = os.environ.get('RDF_DIFFER_API_PORT', '3040'),
