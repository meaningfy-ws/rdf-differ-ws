
import json
import logging
from pathlib import Path
from shutil import copytree

from werkzeug.exceptions import UnprocessableEntity

from rdf_differ.config import RDF_DIFFER_LOGGER

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def generate_report(temp_dir, template_location, dataset, report_builder_class, query_files):
    template_location = str(template_location)
    additional_config = {"conf": {"query_files": query_files,
                                  "default_endpoint": dataset['query_url']}}
    logger.debug(f'template location {template_location}')
    copytree(template_location, temp_dir, dirs_exist_ok=True)

    try:
        with open(Path(temp_dir) / 'config.json', 'r') as config_file:
            config_content = json.load(config_file)

        logger.debug(f'template file {config_content["template"]}')
    except FileNotFoundError as e:
        logger.exception(str(e))
        raise UnprocessableEntity("config.json file is missing from the chosen template variant folder")

    report_builder = report_builder_class(target_path=temp_dir, additional_config=additional_config)
    report_builder.make_document()

    return Path(str(temp_dir)) / 'output', config_content["template"]