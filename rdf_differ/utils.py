"""
utils.py
Date: 09/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
import os
from pathlib import Path
from typing import Union

from rdf_differ import defaults


def get_envs() -> dict:
    return {
        'basedir': os.environ.get('BASEDIR', defaults.BASEDIR),
        'filename': os.environ.get('FILENAME', defaults.FILENAME),
        'endpoint': os.environ['ENDPOINT']
    }


def dir_exists(path: Union[str, Path]) -> bool:
    """
    Method to check the existence of the dir from the indicated path.
    :param path: str or Path
        The path to be checked on.
    :return: bool
        Whether the dir exists or not.
    """
    return Path(path).is_dir()


def dir_is_empty(path: Union[str, Path]) -> bool:
    """
    Method to check if the directory is empty.
    :param path: str or Path
        The path to be checked on.
    :return: bool
        True - dir exists and is empty
        False - any other case
    """
    if dir_exists(path):
        return not any(Path(path).iterdir())

    return False


def file_exists(path: Union[str, Path]) -> bool:
    """
    Method to check the existence of the file from the indicated path.
    :param path: str or Path
        The path to be checked on.
    :return: bool
        Whether the file exists or not.
    """
    return Path(path).is_file()


# TODO: extend dict as required
INPUT_MIME_TYPES = {
    'rdf': 'application/rdf+xml',
    'rdfs': 'application/rdf+xml',
    'owl': 'application/rdf+xml',
    'n3': 'text/n3',
    'ttl': 'text/turtle',
    'json': 'application/json',
}
