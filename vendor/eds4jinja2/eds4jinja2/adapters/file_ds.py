#!/usr/bin/python3

# file_ds.py
# Date:  07/08/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

import json
import pathlib
import yaml
import toml
import pandas as pd

from eds4jinja2.adapters.base_data_source import DataSource, UnsupportedRepresentation

TABULAR_EXTENSIONS = [".csv", ".tsv", ".xlsx", ".xls", ]
TREE_EXTENSIONS = [".json", ".yaml", ".yml", ".toml", ".json-ld", ".jsonld"]


class FileDataSource(DataSource):
    """
        Fetches data from a file. Automatically determines the file type.

        * *Supported tabular file types:* ".csv", ".tsv", ".xlsx", ".xls"
        * *Supported tree file types:* ".json", ".yaml", ".yml", ".toml", ".json-ld", ".jsonld"

        To read a CVS

        >>> ds = FileDataSource("path/to/the/file.csv")
        >>> pd_data_frame, error = ds.fetch_tabular()

        To read a JSON

        >>> ds = FileDataSource("path/to/the/file.json")
        >>> pd_data_frame, error = ds.fetch_tree()
    """

    def __init__(self, file_path):
        self.__file_path = file_path

    @property
    def file_path(self) -> pathlib.Path:
        """
            The location of the DataSource file
        :return:
        """
        return pathlib.Path(self.__file_path)

    @property
    def _file_extension(self):
        return str(self.file_path.suffix).lower()

    def _can_be_tree(self) -> bool:
        return self._file_extension in TREE_EXTENSIONS or self._file_extension in TABULAR_EXTENSIONS

    def _can_be_tabular(self) -> bool:
        return self._file_extension in TABULAR_EXTENSIONS

    def _fetch_tree(self):
        if self._file_extension in [".json", ".json-ld", ".jsonld"]:
            return json.loads(self.file_path.read_bytes())
        elif self._file_extension in [".yaml", ".yml"]:
            return yaml.safe_load(self.file_path.read_bytes())
        elif self._file_extension in [".toml"]:
            return toml.loads(self.file_path.read_bytes())

        if self._can_be_tabular():
            tabular = self._fetch_tabular()
            if isinstance(tabular, pd.DataFrame):
                return json.loads(tabular.to_json())
        raise UnsupportedRepresentation(f"Unsupported tree file type: {self._file_extension}")

    def _fetch_tabular(self):
        if self._file_extension in [".csv", ]:
            return pd.read_csv(self.file_path)
        elif self._file_extension in [".xlsx", ".xls", ".odf", ".ods"]:
            return pd.read_excel(self.file_path, sheet_name=0)
        elif self._file_extension in [".tsv", ]:
            return pd.read_table(self.file_path)
        raise UnsupportedRepresentation(f"Unsupported tabular file type: {self._file_extension}")

    def __str__(self):
        return f"from <...{str(self.__file_path)[-25:]}>"
