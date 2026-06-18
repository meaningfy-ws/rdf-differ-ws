"""Filesystem and RDF-file I/O operations (adapters layer).

Relocated here from the legacy ``rdf_differ.utils`` during the utils dissolution
(DEC-7). This module holds all filesystem-touching helpers (directory/file checks,
copying, listing, saving uploaded files) plus the ``rdflib``-backed RDF conversion
helper. Path-building and meta-file reading used by both the report service and the
diff adapter also live here, since reading a meta file is filesystem I/O and an
adapter consumer (``diff_adapter``) must not import from the services layer.
"""

import logging
import os
import pathlib
import shutil
import tempfile
from contextlib import contextmanager
from json import loads
from pathlib import Path
from typing import cast
from uuid import uuid4

from rdflib.tools.rdfpipe import parse_and_serialize
from werkzeug.datastructures import FileStorage

from rdf_differ.config import RDF_DIFFER_LOGGER
from rdf_differ.domain.naming import build_secure_filename

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def dir_exists(path: str | Path) -> bool:
    """
    Method to check the existence of the dir from the indicated path.
    :param path: str or Path
        The path to be checked on.
    :return: bool
        Whether the dir exists or not.
    """
    return Path(path).is_dir()


def dir_is_empty(path: str | Path) -> bool:
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


def empty_directory(path: str | Path) -> None:
    """
    Method to remove all files from a directory
    :param path: directory to clean
    """
    for item in Path(path).iterdir():
        if item.is_file():
            item.unlink()


def file_exists(path: str | Path) -> bool:
    """
    Method to check the existence of the file from the indicated path.
    :param path: str or Path
        The path to be checked on.
    :return: bool
        Whether the file exists or not.
    """
    return Path(path).is_file()


def copy_file_to_destination(file: str, destination: str) -> str:
    """
    Copy file helper method
    :param file: file to copy
    :param destination: destination to copy
    :return: new file destination
    """
    return shutil.copy(file, destination)


def check_files_exist(file_a: FileStorage, file_b: FileStorage) -> None:
    if not file_a or not file_b:
        raise TypeError("Files cannot be of None type.")


@contextmanager
def save_files(old_file: FileStorage, new_file: FileStorage, location: str = ""):
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
        saved_old_file = build_secure_filename(str(location_to_save), old_file.filename or "")
        saved_new_file = build_secure_filename(str(location_to_save), new_file.filename or "")

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
        saved_old_file = build_secure_filename(temp_dir.name, old_file.filename or "")
        saved_new_file = build_secure_filename(temp_dir.name, new_file.filename or "")

        old_file.save(saved_old_file)
        new_file.save(saved_new_file)

        yield temp_dir.name, saved_old_file, saved_new_file
    finally:
        temp_dir.cleanup()


def list_folders_from_path(path: pathlib.Path) -> list[str]:
    return [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]


def list_files_from_path(path: pathlib.Path) -> list[str]:
    return [x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))]


def list_files_paths_from_path(path: pathlib.Path) -> list[str]:
    """
    Method to list file names from a given path
        :param path:
        The path to be checked on.
    """
    return [str(path / x) for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))]


def list_folder_paths_from_path(path: pathlib.Path) -> list[str]:
    """
    Method to list folder paths from a given path
        :param path:
        The path to be checked on.
    """
    return [str(path / x) for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]


def build_dataset_reports_location(dataset_name: str, reports_location: str) -> str:
    """
    build path for report location of given dataset

    :param dataset_name: dataset name
    :param reports_location: which file system location to use to perform the action
    :return:
    """
    return str(Path(reports_location) / dataset_name)


def read_meta_file(report_base_location: str | Path, meta_file_name: str = "meta.json") -> dict:
    """
    method to read data from meta file
    :param report_base_location: report location
    :param meta_file_name: custom meta name, defaults to "meta.json"
    :return: contents of the meta file
    """
    content = cast(dict, loads((Path(report_base_location) / meta_file_name).read_text()))
    logger.debug(content)
    return content


def convert_test_data(input_file, output_file, input_format="", additional_bindings=None):
    ns_binding = {
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "skosxl": "http://www.w3.org/2008/05/skos-xl#",
        "dct": "http://purl.org/dc/terms/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "euvoc": "http://publications.europa.eu/ontology/euvoc#",
        "lemon": "http://lemon-model.net/lemon#",
        "lexinfo": "http://www.lexinfo.net/ontology/2.0/lexinfo#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "rdf": "http://www.w3.org/2002/07/owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "domain": "http://eurovoc.europa.eu/domain",
        "notation": "http://publications.europa.eu/resource/authority/notation-type",
        "label": "http://publications.europa.eu/resource/authority/label-type",
        "context": "http://publications.europa.eu/resource/authority/use-context",
        "status": "http://publications.europa.eu/resource/authority/concept-status/",
        "p1": "http://inexistent/domain/",
    }

    if additional_bindings:
        ns_binding = {**ns_binding, **additional_bindings}

    guess = not input_format

    parse_and_serialize(
        input_files=[input_file],
        input_format=input_format,
        guess=guess,
        outfile=output_file,
        output_format="ttl",
        ns_bindings=ns_binding,
    )
