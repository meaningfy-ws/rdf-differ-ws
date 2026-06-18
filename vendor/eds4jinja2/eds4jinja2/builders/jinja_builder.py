#!/usr/bin/python3
#
# jinja_builder
# Created:  18/03/2019
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

import jinja2

from eds4jinja2.adapters import invert_dict
from eds4jinja2.adapters.file_ds import FileDataSource
from eds4jinja2.adapters.latex_utils import escape_latex
from eds4jinja2.adapters.local_sparql_ds import RDFFileDataSource
from eds4jinja2.adapters.namespace_handler import NamespaceInventory, simplify_uris_in_tabular
from eds4jinja2.adapters.remote_sparql_ds import RemoteSPARQLEndpointDataSource
from eds4jinja2.adapters.tabular_utils import replace_strings_in_tabular, add_relative_figures

DATA_SOURCE_BUILDERS = {
    "from_endpoint": lambda endpoint: RemoteSPARQLEndpointDataSource(endpoint),
    "from_file": lambda file_path: FileDataSource(file_path),
    "from_rdf_file": lambda from_rdf_file: RDFFileDataSource(from_rdf_file)
}

TABULAR_HELPERS = {
    "invert_dict": lambda mapping_dict, reduce_values=True: invert_dict(mapping_dict, reduce_values),
    "replace_strings_in_tabular": lambda data_frame, target_columns,
                                         value_mapping_dict, mark_touched_rows=False: replace_strings_in_tabular(
        data_frame,
        target_columns,
        value_mapping_dict,
        mark_touched_rows),
    "add_relative_figures": lambda data_frame, target_columns, relativisers, percentage=True: add_relative_figures(
        data_frame,
        target_columns,
        relativisers, percentage),
    "namespace_inventory": lambda namespace_definition_dict: NamespaceInventory(
        namespace_definition_dict=namespace_definition_dict),
    "simplify_uri_columns_in_tabular": lambda data_frame, namespace_inventory, target_columns=None, prefix_cc_lookup=True,
                                       inplace=True, error_fail=True: simplify_uris_in_tabular(
        data_frame,
        namespace_inventory,
        target_columns,
        prefix_cc_lookup,
        inplace,
        error_fail)
}

TREE_HELPERS = {}

ADDITIONAL_FILTERS = {
    "escape_latex": lambda value: escape_latex(value),
}


def build_eds_environment(external_data_source_builders={**DATA_SOURCE_BUILDERS, **TABULAR_HELPERS, **TREE_HELPERS},
                          external_filters=ADDITIONAL_FILTERS, **kwargs):
    """
        creates a JINJA environment and injects the global context with EDS functions
    :param external_filters: additional filters to be make available in the templates
    :param external_data_source_builders: additional instructions to be made available in the templates
    :param kwargs:
    :return:
    """
    template_env = jinja2.Environment(**kwargs)
    inject_environment_globals(template_env, external_data_source_builders)
    inject_environment_filters(template_env, external_filters)
    return template_env


def inject_environment_filters(jinja_environment: jinja2.Environment, filters: dict, update_existent=True):
    """
        Inject the filters into JINJA2 environment making them globally available from any template.
        Updates in place the `filter` environment dictionary by adding non existent keys from another dictionary.
        If the dictionary keys exist then they are replaced depending whether the update_existent flag is set.
    :param update_existent: whether the overlapping values shall be overwritten
    :param filters: additional filters to be injected
    :param jinja_environment: JINJA environment to be updated
    :return:
    """
    if update_existent:
        jinja_environment.filters.update(filters)
    else:
        jinja_environment.filters.update(
            {k: v for k, v in filters.items() if k not in jinja_environment.filters.keys()})


def inject_environment_globals(jinja_environment: jinja2.Environment, context: dict, update_existent=True):
    """
        Inject the context into JINJA2 environment making it globally available from any template.
        Updates in place the `global` environment dictionary by adding non existent keys from another dictionary.
        If the keys exist then they are replaced depending whether the update_existent flag is set.
    :param update_existent: whether the overlapping values shall be overwritten
    :param context: additional context to be injected
    :param jinja_environment: JINJA environment to be updated
    :return:
    """
    if update_existent:
        jinja_environment.globals.update(context)
    else:
        jinja_environment.globals.update(
            {k: v for k, v in context.items() if k not in jinja_environment.globals.keys()})
