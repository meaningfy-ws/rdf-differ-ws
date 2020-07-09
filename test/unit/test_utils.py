"""
test_utils.py
Date: 09/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""

from pathlib import Path


def test_dir_exists():
    from rdf_differ.utils import dir_exists

    test_path = Path.cwd().joinpath('test_path')
    test_path.mkdir()

    assert dir_exists(test_path) is True

    test_path.rmdir()


def test_dir_doesnt_exist():
    from rdf_differ.utils import dir_exists

    test_path = Path.cwd().joinpath('test_path')

    assert dir_exists(test_path) is False
