"""
test_file_utils.py
Date: 09/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from io import BytesIO
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage

from rdf_differ.config import get_envs
from tests.unit.conftest import helper_endpoint_mock
from utils.file_utils import dir_exists, file_exists, dir_is_empty, temporarily_save_files


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


def test_temporarily_save_files_success():
    location = None
    with temporarily_save_files(FileStorage((BytesIO(b'1')), filename='old_file'),
                                FileStorage((BytesIO(b'2')), filename='new_file')) \
            as (temp_dir, old_file, new_file):
        location = temp_dir
        assert dir_exists(location)

        with open(old_file) as file:
            assert file.read() == '1'
        with open(new_file) as file:
            assert file.read() == '2'

    assert not dir_exists(location)


@pytest.mark.parametrize("file_1, file_2", [(FileStorage((BytesIO(b'1')), filename='old_file'), None),
                                            (None, FileStorage((BytesIO(b'2')), filename='new_file')),
                                            (None, None)])
def test_temporarily_save_files_failure(file_1, file_2):
    with pytest.raises(TypeError):
        with temporarily_save_files(file_1, file_2):
            pass
