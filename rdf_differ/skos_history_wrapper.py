"""
skos_history_wrapper.py
Date: 06/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
from pathlib import Path
from shutil import copy
from urllib.parse import urljoin

from rdflib.util import guess_format

from utils.file_utils import INPUT_MIME_TYPES, dir_exists, dir_is_empty


class SKOSHistoryFolderSetUp:
    def __init__(self, dataset: str, filename: str, alpha_file: str, beta_file: str, root_path: str,
                 version_name1: str = 'v1', version_name2: str = 'v2'):
        self.dataset = dataset
        self.filename = filename
        self.alpha_file = alpha_file
        self.beta_file = beta_file
        self.root_path = root_path
        self.version_name1 = version_name1
        self.version_name2 = version_name2

        self._check_root_path()

    def generate(self):
        v1 = Path(self.root_path) / self.dataset / 'data' / self.version_name1
        v2 = Path(self.root_path) / self.dataset / 'data' / self.version_name2
        v1.mkdir(parents=True)
        v2.mkdir(parents=True)

        copy(self.alpha_file, v1 / self.filename)
        copy(self.beta_file, v2 / self.filename)

    def _check_root_path(self):
        if dir_exists(self.root_path) and not dir_is_empty(self.root_path):
            raise Exception('Root path is not empty.')


class SKOSHistoryRunner:
    def __init__(self, dataset: str, scheme_uri: str, versions: list, basedir: str, filename: str, endpoint: str,
                 config_template_location: str = '../templates/template.config'):
        self.config_template = self._read_file(config_template_location)
        self.dataset = dataset
        self.scheme_uri = scheme_uri
        self.versions = versions

        self.basedir = basedir
        self.filename = filename
        self.endpoint = endpoint

    @property
    def put_uri(self) -> str:
        """
        Build the PUT URI
        :return: str
            PUT URI
        """
        return urljoin(self.endpoint, '/'.join([self.dataset, 'data']))

    @property
    def update_uri(self) -> str:
        """
        Build the update URI
        :return: str
            UPDATE URI
        """
        return urljoin(self.endpoint, self.dataset)

    @property
    def query_uri(self) -> str:
        """
        Build the query URI
        :return: str
            query URI
        """
        return urljoin(self.endpoint, '/'.join([self.dataset, 'query']))

    @property
    def input_file_mime(self) -> str:
        file_format = guess_format(self.filename, INPUT_MIME_TYPES)
        if file_format is None:
            raise Exception('File type not supported.')

        return file_format

    def generate(self) -> str:
        content = self.config_template.format(
            dataset=self.dataset,
            scheme_uri=self.scheme_uri,
            versions='({} {})'.format(*self.versions),
            basedir=self.basedir,
            filename=self.filename,
            put_uri=self.put_uri,
            update_uri=self.update_uri,
            query_uri=self.query_uri,
            input_type=self.input_file_mime
        )
        location = Path(self.basedir) / '{}.config'.format(self.dataset)
        with open(location, 'w') as file:
            file.write(content)

        return str(location)

    @staticmethod
    def _read_file(relative_location):
        location = Path(__file__).parent / relative_location
        with open(location, 'r') as file:
            content = file.read()
        return content
