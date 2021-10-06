#!/usr/bin/python3

# test_file_utils.py
# Date: 09/07/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

from io import BytesIO
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage

from utils.file_utils import dir_exists, file_exists, dir_is_empty, temporarily_save_files, save_files, \
    check_files_exist


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


def test_save_files_success(tmpdir):
    location = tmpdir.mkdir('db')
    with save_files(FileStorage((BytesIO(b'1')), filename='old_file'),
                    FileStorage((BytesIO(b'2')), filename='new_file'),
                    location) \
            as (storage_location, old_file, new_file):
        location = storage_location
        assert dir_exists(location)

        with open(old_file) as file:
            assert file.read() == '1'
        with open(new_file) as file:
            assert file.read() == '2'

    assert dir_exists(location)


@pytest.mark.parametrize("file_1, file_2", [(FileStorage((BytesIO(b'1')), filename='old_file'), None),
                                            (None, FileStorage((BytesIO(b'2')), filename='new_file')),
                                            (None, None)])
def test_check_files_exist_failure(file_1, file_2):
    with pytest.raises(TypeError):
        check_files_exist(file_1, file_2)
