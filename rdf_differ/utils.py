"""
utils.py
Date: 09/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""

from pathlib import Path
from typing import Union


def dir_exists(path: Union[str, Path]) -> bool:
    """
    Method to check the existence of the dir from the indicated path.
    :param path: str or Path
        The path to be checked on.
    :return: bool
        Whether the dir exists or not.
    """
    return Path(path).is_dir()


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
