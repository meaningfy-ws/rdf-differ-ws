#!/usr/bin/python3

# file_utils.py
# Date: 09/07/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Union
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from rdf_differ.config import RDF_DIFFER_LOGGER

logger = logging.getLogger(RDF_DIFFER_LOGGER)


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
def save_files(old_file: FileStorage, new_file: FileStorage, location: str = ''):
    """
    Context manager that accepts 2 files and saved them in a temporary directory that gets removed after the context
    closes.
    :param old_file: file to be saved in the temporary directory
    :param new_file: file to be saved in the temporary directory
    :param location: location to store files
    """
    if not old_file or not new_file:
        raise TypeError("Files cannot be of None type.")

    if not location:
        raise TypeError("Location can't be null")

    location_to_save = Path(location) / str(uuid4())
    location_to_save.mkdir()
    try:
        saved_old_file = location_to_save / (str(uuid4()) + secure_filename(old_file.filename))
        saved_new_file = location_to_save / (str(uuid4()) + secure_filename(new_file.filename))

        old_file.save(str(saved_old_file))
        new_file.save(str(saved_new_file))

        yield location_to_save, saved_old_file, saved_new_file
    except Exception as e:
        logger.error(str(e))


@contextmanager
def temporarily_save_files(old_file: FileStorage, new_file: FileStorage):
    """
    Context manager that accepts 2 files and saved them in a temporary directory that gets removed after the context
    closes.
    :param old_file: file to be saved in the temporary directory
    :param new_file: file to be saved in the temporary directory
    """
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
