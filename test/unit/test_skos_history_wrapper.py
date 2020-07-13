"""
test_skos_history_wrapper.py
Date: 06/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""

import pytest

from rdf_differ import defaults
from rdf_differ.skos_history_wrapper import SKOSHistoryRunner


def helper_endpoint_mock(monkeypatch):
    monkeypatch.setenv('ENDPOINT', 'http://test.point')


@pytest.fixture
def mock_env_basedir(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.setenv('BASEDIR', '/basedir')


def test_basedir_exists(mock_env_basedir):
    skos_runner = SKOSHistoryRunner()
    assert skos_runner.basedir == '/basedir'


@pytest.fixture
def mock_env_basedir_missing(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.delenv("BASEDIR", raising=False)


def test_basedir_doesnt_exist(mock_env_basedir_missing):
    skos_runner = SKOSHistoryRunner()
    assert skos_runner.basedir == defaults.BASEDIR


@pytest.fixture
def mock_env_filename(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.setenv('FILENAME', 'test.rdf')


def test_filename_exists(mock_env_filename):
    skos_runner = SKOSHistoryRunner()
    assert skos_runner.filename == 'test.rdf'


@pytest.fixture
def mock_env_filename_missing(monkeypatch):
    helper_endpoint_mock(monkeypatch)
    monkeypatch.delenv("FILENAME", raising=False)


def test_filename_doesnt_exist(mock_env_filename_missing):
    skos_runner = SKOSHistoryRunner()
    assert skos_runner.filename == defaults.FILENAME


@pytest.fixture
def mock_env_endpoint(monkeypatch):
    helper_endpoint_mock(monkeypatch)


def test_endpoint_exists(mock_env_endpoint):
    skos_runner = SKOSHistoryRunner()
    assert skos_runner.endpoint == 'http://test.point'


@pytest.fixture
def mock_env_endpoint_missing(monkeypatch):
    monkeypatch.delenv("ENDPOINT", raising=False)


def test_endpoint_doesnt_exist(mock_env_endpoint_missing):
    with pytest.raises(KeyError) as key_error:
        skos_runner = SKOSHistoryRunner()

    assert 'ENDPOINT' in str(key_error.value)


class TestSKOSHistoryRunnerBuildURIs:
    def setup_method(self):
        self.skos_runner = SKOSHistoryRunner()

    def test_endpoint_exists_dataset_exists(self):
        self.skos_runner.endpoint = 'http://test.point'
        self.skos_runner.dataset = 'dataset'

        assert self.skos_runner.put_uri == 'http://test.point/dataset/data'
        assert self.skos_runner.update_uri == 'http://test.point/dataset'
        assert self.skos_runner.query_uri == 'http://test.point/dataset/query'

    def test_endpoint_doesnt_dataset_exists(self):
        self.skos_runner.dataset = 'dataset'

        assert self.skos_runner.put_uri == 'http://test.point/dataset/data'
        assert self.skos_runner.update_uri == 'http://test.point/dataset'
        assert self.skos_runner.query_uri == 'http://test.point/dataset/query'
