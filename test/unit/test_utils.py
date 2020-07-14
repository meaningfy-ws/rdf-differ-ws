"""
test_utils.py
Date: 09/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""

from pathlib import Path

from rdf_differ.utils import dir_exists, file_exists


def test_dir_exists():
    test_path = Path.cwd().joinpath('test_path')
    test_path.mkdir()

    assert dir_exists(test_path) is True

    test_path.rmdir()


def test_dir_doesnt_exist():
    test_path = Path.cwd().joinpath('test_path')

    assert dir_exists(test_path) is False


def test_file_exists():
    test_path = Path.cwd().joinpath('test_file')
    test_path.touch()

    assert file_exists(test_path) is True

    test_path.unlink()


def test_file_doesnt_exist():
    test_path = Path.cwd().joinpath('test_file')

    assert file_exists(test_path) is False
