"""
test_file_utils.py
Date: 09/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""

from pathlib import Path

import pytest

from tests.unit.conftest import helper_endpoint_mock
from utils.file_utils import dir_exists, file_exists, dir_is_empty
from rdf_differ.config import get_envs


def test_read_envs_basedir_exists(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.setenv('BASEDIR', '/basedir')

    envs = get_envs()
    assert envs['basedir'] == '/basedir'


def test_read_envs_basedir_doesnt_exist(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.delenv("BASEDIR", raising=False)

    envs = get_envs()
    assert envs['basedir'] == './basedir'


def test_read_envs_filename_exists(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.setenv('FILENAME', 'tests.rdf')

    envs = get_envs()
    assert envs['filename'] == 'tests.rdf'


def test_read_envs_filename_doesnt_exist(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.delenv("FILENAME", raising=False)

    envs = get_envs()
    assert envs['filename'] == 'file'


def test_read_envs_endpoint_exists(monkeypatch):
    helper_endpoint_mock(monkeypatch)

    envs = get_envs()
    assert envs['endpoint'] == 'http://test.point'


def test_read_envs_endpoint_doesnt_exist(monkeypatch):
    monkeypatch.delenv("ENDPOINT", raising=False)

    with pytest.raises(KeyError) as key_error:
        _ = get_envs()

    assert 'ENDPOINT' in str(key_error.value)


def test_dir_exists(tmpdir):
    test_path = tmpdir.mkdir('test_path')

    assert dir_exists(test_path) is True


def test_dir_doesnt_exist():
    # .joinpath doesn't create the folder.
    # it's an easier way to get full path of something.
    test_path = Path.cwd().joinpath('test_path')

    assert dir_exists(test_path) is False


def test_dir_exists_is_empty(tmpdir):
    test_path = tmpdir.mkdir('test_path')

    assert dir_is_empty(test_path) is True


def test_dir_exists_doesnt_exist(tmpdir):
    test_path = Path.cwd().joinpath('test_path')

    assert dir_is_empty(test_path) is False


def test_dir_exists_is_not_empty(tmpdir):
    test_path = tmpdir.mkdir('test_path')
    file = test_path.join('file')
    file.write('')

    assert dir_is_empty(test_path) is False


def test_file_exists(tmpdir):
    test_path = tmpdir.join('test_file')
    test_path.write('')

    assert file_exists(test_path) is True


def test_file_doesnt_exist():
    test_path = Path.cwd().joinpath('test_file')

    assert file_exists(test_path) is False
