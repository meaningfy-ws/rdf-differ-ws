"""
test_utils.py
Date: 09/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""

from pathlib import Path

import pytest

from rdf_differ import defaults
from rdf_differ.utils import dir_exists, file_exists, dir_is_empty, get_envs


def helper_endpoint_mock(monkeypatch):
    monkeypatch.setenv('ENDPOINT', 'http://test.point')


@pytest.fixture
def mock_env_basedir(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.setenv('BASEDIR', '/basedir')


def test_read_envs_basedir_exists(mock_env_basedir):
    envs = get_envs()
    assert envs['basedir'] == '/basedir'


@pytest.fixture
def mock_env_basedir_missing(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.delenv("BASEDIR", raising=False)


def test_read_envs_basedir_doesnt_exist(mock_env_basedir_missing):
    envs = get_envs()
    assert envs['basedir'] == defaults.BASEDIR


@pytest.fixture
def mock_env_filename(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.setenv('FILENAME', 'test.rdf')


def test_read_envs_filename_exists(mock_env_filename):
    envs = get_envs()
    assert envs['filename'] == 'test.rdf'


@pytest.fixture
def mock_env_filename_missing(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.delenv("FILENAME", raising=False)


def test_read_envs_filename_doesnt_exist(mock_env_filename_missing):
    envs = get_envs()
    assert envs['filename'] == defaults.FILENAME


@pytest.fixture
def mock_env_endpoint(monkeypatch):
    helper_endpoint_mock(monkeypatch)


def test_read_envs_endpoint_exists(mock_env_endpoint):
    envs = get_envs()
    assert envs['endpoint'] == 'http://test.point'


@pytest.fixture
def mock_env_endpoint_missing(monkeypatch):
    monkeypatch.delenv("ENDPOINT", raising=False)


def test_read_envs_endpoint_doesnt_exist(mock_env_endpoint_missing):
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
