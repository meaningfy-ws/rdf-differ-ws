import os
import pathlib


def list_folders_from_path(path: pathlib.Path):
    return [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]


def list_files_from_path(path: pathlib.Path):
    return [x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))]
