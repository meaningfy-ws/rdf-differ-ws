"""
config.py
Date: 20/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
import os


def get_envs() -> dict:
    return {
        'filename': os.environ.get('FILENAME', 'file'),
        'endpoint': os.environ.get('ENDPOINT', 'http://localhost:3030')
    }


RDF_DIFFER_API_PORT = os.environ.get('RDF_DIFFER_API_PORT', '3040'),
