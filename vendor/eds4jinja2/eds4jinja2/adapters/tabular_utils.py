#!/usr/bin/python3

# tabular_utils.py
# Date:  17/08/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" a set of helper functions to easily polish the tabular data (i.e Pandas DataFrame) """
import re
from typing import List, Dict

import pandas as pd
import numpy as np
import logging

from pandas.core.dtypes.common import is_numeric_dtype

logger = logging.getLogger(__name__)


def replace_strings_in_tabular(data_frame: pd.DataFrame, target_columns: List[str] = None,
                               value_mapping_dict: Dict = None,
                               mark_touched_rows: bool = False) -> List[str]:
    """
        Replaces the values from the target columns in a data frame according to the value-mapping dictionary.
        If the inverted_mapping flag is true, then the inverted value_mapping_dict is considered.
        If mark_touched_rows is true, then adds a boolean column _touched_ where

        >>> mapping_dict example = {"old value 1" : "new value 1", "old value 2":"new value 2"}

        :param mark_touched_rows: add a new boolean column _touched_ indicating which rows were updated
        :param value_mapping_dict: the string substitution mapping
        :param target_columns: a list of column names otehrwise leave empty if substitution applies to all columns
        :param data_frame: the data frame
        :return the list of unique strings found in the dataframe
    """
    if not target_columns:
        target_columns = []
    if not value_mapping_dict:
        value_mapping_dict = {}

    for col in target_columns:
        if col not in data_frame.columns.values.tolist():
            raise ValueError("The target column not found in the data frame")
    # get all the string columns
    obj_columns = data_frame.select_dtypes([object]).columns  # [1:]
    # columns = self.target_columns if self.target_columns else self.data_frame.columns
    # limit to columns indicated in the self.target_columns
    if target_columns:
        obj_columns = [column for column in obj_columns if column in target_columns]

    # The URIs contains special regex chars, better to escape them when searching through dataframe
    escaped_value_mapping_dict = {r"" + re.escape(k): v for k, v in value_mapping_dict.items()}

    # add a column flagging touched rows
    if mark_touched_rows:
        mask = np.column_stack(
            [data_frame[col].str.contains('(' + '|'.join(escaped_value_mapping_dict.keys()) + ')', na=False)
             for col in obj_columns])
        data_frame["_touched_"] = np.logical_or.reduce(mask, axis=1)
        # data_frame["_found_"] = found_strings_column_stack

    # which (unique) strings are found in the dataframe?
    strings_found_column_stack = np.array(
        [data_frame[col].str.findall('(' + '|'.join(escaped_value_mapping_dict.keys()) + ')',
                                     flags=re.IGNORECASE).values
         for col in obj_columns]
    )
    strings_found = np.unique(np.concatenate(strings_found_column_stack.flatten()))

    # create a nested dictionary that pandas replace understand
    # For a DataFrame nested dictionaries, e.g., {'a': {'b': np.nan}}, are read as
    # follows: look in column ‘a’ for the value ‘b’ and replace it with NaN. The
    # optional value parameter should not be specified to use a nested dict in this
    # way.
    nested_dict = {column: escaped_value_mapping_dict for column in obj_columns}

    # this is the way to do it for pandas >1.4.2, aligned with official docs
    data_frame.replace(to_replace=None, regex=nested_dict, inplace=True)
    # this apparently also works but is not aligned with official docs
    # data_frame.replace(to_replace=nested_dict, regex=True, inplace=True)

    return strings_found


def add_relative_figures(data_frame: pd.DataFrame, target_columns: List[str], relativisers: List,
                         percentage: bool = True):
    """
        For each target_columns add a calculate column with relative values calculated
        based on the provided relativisers.


    :param percentage:
    :param data_frame:
    :param target_columns:
    :param relativisers: a list of indicators corresponding to the *target_columns*
            comprising either *None*, a *number* or a *column name*
    :return:
    """
    # Some sanity checkers
    if len(relativisers) > len(target_columns):
        raise ValueError("There cannot be more relativisers than target columns")

    for rel in relativisers:
        if isinstance(rel, str):
            if rel not in data_frame.columns.values.tolist():
                raise ValueError("The relativiser column not found in the data frame")
            if not is_numeric_dtype(data_frame[rel]):
                raise ValueError("The relativiser column is not of numeric type")
        elif not (is_numeric_dtype(type(rel)) or rel is None):
            raise ValueError("The relativiser must be a number, None or a column name.")

    for col in target_columns:
        if col not in data_frame.columns.values.tolist():
            raise ValueError("The target column not found in the data frame")
        if not is_numeric_dtype(data_frame[col]):
            raise ValueError("The target column is not of numeric type")
    # End of sanity checkers

    new_columns = [c + "_relative" if not isinstance(r, str) else c + "_relative_to_" + r for c, r in
                   zip(target_columns, relativisers)]

    for (new_col, old_col, relativiser) in zip(new_columns, target_columns, relativisers):
        if not relativiser:
            relativiser = data_frame[old_col].sum()
        elif isinstance(relativiser, str):
            relativiser = data_frame[relativiser]

        if percentage:
            data_frame[new_col] = data_frame[old_col] * 100 / relativiser
        else:
            data_frame[new_col] = data_frame[old_col] / relativiser
