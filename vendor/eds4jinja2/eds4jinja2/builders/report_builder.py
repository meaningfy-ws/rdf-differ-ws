#!/usr/bin/python3

# report_generator
# Created:  08/03/2019
# Author: Laurentiu Mandru
# Email: mclaurentiu79@gmail.com

"""
this module implements the report generation functionality.
"""
import json
import pathlib
from typing import Union

import jinja2

from eds4jinja2.adapters import deep_update
from eds4jinja2.builders.jinja_builder import build_eds_environment, inject_environment_globals

# aims to be close to the J2 default env syntax definition, but explicitly specified
HTML_TEMPLATE_SYNTAX = {'block_start_string': '{%',
                        'block_end_string': '%}',
                        'variable_start_string': '{{',
                        'variable_end_string': '}}',
                        'comment_start_string': '{#',
                        'comment_end_string': '#}',
                        'line_statement_prefix': '#',
                        'line_comment_prefix': '##',
                        'trim_blocks': False, }

# do not change anything
DEFAULT_TEMPLATE_SYNTAX = {}

######################################################################
# Jinja2 Environment ARGS
#   Constant borrowed from Marc Brinkmann's latex repository (mbr/latex on github)
#   Reused also by Samuel Roeca's in his latex repository (pappasam/latexbuild on github)
######################################################################
LATEX_TEMPLATE_SYNTAX = {'block_start_string': r'\BLOCK{',
                         'block_end_string': '}',
                         'variable_start_string': r'\VAR{',
                         'variable_end_string': '}',
                         'comment_start_string': r'\#{',
                         'comment_end_string': '}',
                         'line_statement_prefix': '%-',
                         'line_comment_prefix': '%#',
                         'trim_blocks': True,
                         'autoescape': False, }


class ReportBuilder:
    """
        generic report builder that takes templates and configuration as input and produces an output report
    """
    configuration_context: dict = {}

    def __init__(self, target_path: Union[str, pathlib.Path], config_file: str = "config.json",
                 output_path: str = None, additional_config: dict = {}):
        """
            Instantiates builders form a template providing an optional configuration context.

        :type additional_config: additional config parameters that are added to the default
                                ones be overwritten (deep update) in the project config.json
        :param target_path: the folder where the required resources are found
        :param config_file: the configuration file (default 'config.json')
        :param output_path: the output folder where the result of the rendering will be created
        """

        with open(pathlib.Path(target_path) / config_file, encoding='utf-8') as configFile:
            self.configuration_context = json.loads(configFile.read())
        deep_update(self.configuration_context, additional_config)

        template_path = str(pathlib.Path(target_path) / "templates")
        static_folder = pathlib.Path(target_path) / "static"
        if output_path is not None:
            output_folder = pathlib.Path(output_path)
        else:
            # in case you don't specify an output, the rendered content will be placed
            # in the target folder, in an default directory named "output"
            # this is to prevent creating files wherever you happen to run the CLI
            output_folder = pathlib.Path(target_path) / "output"

        self.configuration_context["template_path"] = template_path
        self.configuration_context["static_folder"] = str(static_folder)
        self.configuration_context["output_folder"] = str(output_folder)
        self.configuration_context["conf"]["template_path"] = template_path
        self.template = self.configuration_context["template"]

        # Provides a configuration of the templating syntax flavour. By default it is configured
        # for HTML but could be adapted as necessary. For LaTex, LATEX_TEMPLATE_SYNTAX is available.
        # TODO: this code might need to be externalised in the next refactoring
        if "template_flavour_syntax" in self.configuration_context:
            if str.lower(self.configuration_context["template_flavour_syntax"]) in ("latex", "tex"):
                self.template_flavour_syntax_spec = LATEX_TEMPLATE_SYNTAX
            elif str.lower(self.configuration_context["template_flavour_syntax"]) in ("xml", "html", "xhtml"):
                self.template_flavour_syntax_spec = HTML_TEMPLATE_SYNTAX
            else:
                self.template_flavour_syntax_spec = DEFAULT_TEMPLATE_SYNTAX
        else:
            self.template_flavour_syntax_spec = DEFAULT_TEMPLATE_SYNTAX

        template_loader = jinja2.FileSystemLoader(searchpath=template_path)
        self.template_env = build_eds_environment(loader=template_loader, **self.template_flavour_syntax_spec)
        inject_environment_globals(self.template_env, {'conf': self.configuration_context["conf"]},
                                   False if self.configuration_context is None else True)

        self.__before_rendering_listeners = []
        self.__after_rendering_listeners = []

    def add_before_rendering_listener(self, listener):
        """
            At the moment there is no use for this.
        """
        self.__before_rendering_listeners.append(listener)

    def add_after_rendering_listener(self, listener):
        """
            At the moment, this is used just to copy static files to the output directory.
            For example, CSS, JavaScript and other static resources.
        """
        self.__after_rendering_listeners.append(listener)

    def __get_template(self, template_name=None) -> jinja2.Template:
        """
            Standard JINJA2 get_template() functionality.
        :param template_name:
        :return:
        """
        if not template_name:
            return self.template_env.get_template(self.template)
        else:
            return self.template_env.get_template(template_name)

    def make_document(self):
        for listener in self.__before_rendering_listeners:
            listener(self.configuration_context)

        template = self.__get_template(self.template)

        pathlib.Path(self.configuration_context["output_folder"]).mkdir(parents=True, exist_ok=True)
        template.stream().dump(str(pathlib.Path(self.configuration_context["output_folder"]) / self.template))

        for listener in self.__after_rendering_listeners:
            listener(self.configuration_context)
