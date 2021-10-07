import logging
from json import dumps
from pathlib import Path
from shutil import copytree

from rdf_differ.config import RDF_DIFFER_LOGGER
from rdf_differ.services.validation import get_application_profile_location
from rdf_differ.entrypoints.api.handlers_helpers import generate_report_builder_config

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def generate_report(temp_dir, application_profile, dataset, report_builder_class):
    template_location = get_application_profile_location(application_profile)
    logger.debug(f'template location {template_location}')
    copytree(template_location, temp_dir, dirs_exist_ok=True)

    with open(Path(temp_dir) / 'config.json', 'w') as config_file:
        config_content = generate_report_builder_config(template_location, dataset)
        config_file.write(dumps(config_content))

    report_builder = report_builder_class(target_path=temp_dir)
    report_builder.make_document()

    return Path(str(temp_dir)) / 'output', 'main.html'
