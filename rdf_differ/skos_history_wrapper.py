"""
skos_history_wrapper.py
Date: 06/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
import logging
from subprocess import Popen, PIPE, STDOUT
from pathlib import Path
from shutil import copy
from typing import Union
from urllib.parse import urljoin, quote

from rdflib.util import guess_format

from rdf_differ.config import get_envs
from utils.file_utils import INPUT_MIME_TYPES, dir_exists, dir_is_empty

CONFIG_TEMPLATE = """#!/bin/bash

DATASET={dataset}
SCHEMEURI=\"{scheme_uri}\"

VERSIONS={versions}
BASEDIR={basedir}
FILENAME={filename}

PUT_URI={put_uri}
UPDATE_URI={update_uri}
QUERY_URI={query_uri}

INPUT_MIME_TYPE=\"{input_type}\""""


class SKOSHistoryRunner:
    def __init__(self, dataset: str, scheme_uri: str, basedir: str, filename: str, endpoint: str,
                 old_version_file: str, new_version_file: str, old_version_id: str, new_version_id: str,
                 config_template: str = CONFIG_TEMPLATE):
        """
        Class for running the skos-history shell script.
        It includes folder structure creation and config file population.

        :param dataset: the name used
        :param scheme_uri: the concept scheme or dataset URI
        :param basedir: location for folder generation
        :param filename: the name of the file to be used for upload
        (its extension will not be taken into consideration if given)
        :param endpoint: upload url
        :param old_version_file: the location of the file to be uploaded
        :param new_version_file: the location of the file to be uploaded
        :param old_version_id: name used for diff upload
        :param new_version_id: name used for diff upload
        :param config_template: string

        file_format: format of the files used, as defined in INPUT_MIME_TYPES
        file_extension: extension of the files used, as defined in INPUT_MIME_TYPES
        """
        if not (dataset and scheme_uri and old_version_file and old_version_id and new_version_file and new_version_id):
            raise Exception('These parameters cannot be empty:'
                            f'{" dataset" if not dataset else ""}'
                            f'{" scheme_uri" if not scheme_uri else ""}'
                            f'{" old_version_file" if not old_version_file else ""}'
                            f'{" old_version_id" if not old_version_id else ""}'
                            f'{" new_version_file" if not new_version_file else ""}'
                            f'{" new_version_id." if not new_version_id else "."}')

        self.config_template = config_template
        self.dataset = quote(dataset)
        self.scheme_uri = scheme_uri

        self.old_version_file = old_version_file
        self.new_version_file = new_version_file
        self.old_version_id = old_version_id
        self.new_version_id = new_version_id

        self.basedir = basedir if basedir else get_envs().get('basedir')
        self.filename = filename if filename else get_envs().get('filename')
        self.endpoint = endpoint if endpoint else get_envs().get('endpoint')

        self._check_basedir()

        self.file_format = self._check_file_formats()
        self.file_extension = Path(self.old_version_file).suffix

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

    @staticmethod
    def get_file_format(file: str) -> str:
        file_format = guess_format(file, INPUT_MIME_TYPES)
        if file_format is None:
            raise Exception('Format of "{}" is not supported.'.format(file))

        return file_format

    def run(self):
        self.generate_structure()
        config_location = self.generate_config()
        self.execute_subprocess(config_location)

    def generate_structure(self):
        v1 = Path(self.basedir) / self.old_version_id
        v2 = Path(self.basedir) / self.new_version_id

        v1.mkdir(parents=True)
        v2.mkdir(parents=True)

        copy(self.old_version_file, v1 / self._get_full_filename())
        copy(self.new_version_file, v2 / self._get_full_filename())

    def generate_config(self) -> str:
        content = self.config_template.format(
            dataset=self.dataset,
            scheme_uri=self.scheme_uri,
            versions='({} {})'.format(self.old_version_id, self.new_version_id),
            basedir=self.basedir,
            filename=self._get_full_filename(),
            put_uri=self.put_uri,
            update_uri=self.update_uri,
            query_uri=self.query_uri,
            input_type=self.file_format
        )
        location = Path(self.basedir) / f'{self.dataset}.config'
        with open(location, 'w') as file:
            file.write(content)

        return str(location)

    def _get_full_filename(self):
        return '{}{}'.format(self.filename, self.file_extension)

    def _check_file_formats(self):
        old_format = self.get_file_format(self.old_version_file)
        new_format = self.get_file_format(self.new_version_file)

        if old_format != new_format:
            raise Exception(f'File formats are different: {old_format}, {new_format}')

        return old_format

    def _check_basedir(self):
        if dir_exists(self.basedir) and not dir_is_empty(self.basedir):
            raise Exception('Root path is not empty.')

    @classmethod
    def execute_subprocess(cls, config_location: Union[str, Path]) -> str:
        script_location = Path(__file__).parent.parent / 'resources/load_versions.sh'

        logging.info('Subprocess: run load_versions.sh start.')

        process = Popen(
            [script_location, '-f', config_location],
            stdout=PIPE)
        output, _ = process.communicate()

        if process.returncode != 0:
            logging.info('Subprocess: load_versions.sh failed.')
            raise Exception(output)

        logging.info('Subprocess: load_versions.sh finished successful.')
        return output.decode()
