"""
file_utils.py
Date: 09/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Union
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


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


@contextmanager
def temporarily_save_files(old_file: FileStorage, new_file: FileStorage):
    if not old_file or not new_file:
        raise TypeError("Files cannot be of None type.")

    temp_dir = tempfile.TemporaryDirectory()
    try:
        saved_old_file = Path(temp_dir.name) / (str(uuid4()) + secure_filename(old_file.filename))
        saved_new_file = Path(temp_dir.name) / (str(uuid4()) + secure_filename(new_file.filename))

        old_file.save(saved_old_file)
        new_file.save(saved_new_file)

        yield Path(temp_dir.name), saved_old_file, saved_new_file
    finally:
        temp_dir.cleanup()


INPUT_MIME_TYPES = {
    'rdf': 'application/rdf+xml',
    'trix': 'application/xml',
    'nq': 'application/n-quads',
    'nt': 'application/n-triples',
    'jsonld': 'application/ld+json',
    'n3': 'text/n3',
    'ttl': 'text/turtle',
}
