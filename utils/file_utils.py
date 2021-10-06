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


def check_files_exist(file_a: FileStorage, file_b: FileStorage) -> None:
    if not file_a or not file_b:
        raise TypeError("Files cannot be of None type.")


def build_secure_filename(location: str, filename: str) -> str:
    return str(Path(location) / (str(uuid4()) + secure_filename(filename)))


@contextmanager
def save_files(old_file: FileStorage, new_file: FileStorage, location: str = ''):
    """
    Context manager that accepts 2 files and saved them in the specified directory
    :param old_file: file to be saved
    :param new_file: file to be saved
    :param location: location to store files
    """

    if not location:
        raise TypeError("Location can't be null")

    check_files_exist(old_file, new_file)

    location_to_save = Path(location) / str(uuid4())
    location_to_save.mkdir()
    try:
        saved_old_file = build_secure_filename(str(location_to_save), old_file.filename)
        saved_new_file = build_secure_filename(str(location_to_save), new_file.filename)

        old_file.save(str(saved_old_file))
        new_file.save(str(saved_new_file))

        yield str(location_to_save), saved_old_file, saved_new_file
    except Exception as e:
        logger.error(str(e))
        raise ValueError(str(e))


@contextmanager
def temporarily_save_files(old_file: FileStorage, new_file: FileStorage):
    """
    Context manager that accepts 2 files and saved them in a temporary directory that gets removed after the context
    closes.
    :param old_file: file to be saved in the temporary directory
    :param new_file: file to be saved in the temporary directory
    """
    check_files_exist(old_file, new_file)

    temp_dir = tempfile.TemporaryDirectory()
    try:
        saved_old_file = build_secure_filename(temp_dir.name, old_file.filename)
        saved_new_file = build_secure_filename(temp_dir.name, new_file.filename)

        old_file.save(saved_old_file)
        new_file.save(saved_new_file)

        yield temp_dir.name, saved_old_file, saved_new_file
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
