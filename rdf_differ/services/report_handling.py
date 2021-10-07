import json
import logging
from json import dumps
from pathlib import Path
from shutil import copytree

from eds4jinja2.builders.report_builder import ReportBuilder

from rdf_differ.config import RDF_DIFFER_LOGGER, RDF_DIFFER_REPORTS_DB
from rdf_differ.config import get_application_profile_location
from utils.file_utils import dir_is_empty, empty_directory, copy_file_to_destination, dir_exists

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def generate_report_builder_config(template_location, dataset: dict):
    config_dict = json.loads((Path(template_location) / "config.json").read_bytes())
    config_dict["conf"]["default_endpoint"] = dataset['query_url']
    return config_dict


def build_report(temp_dir: str, dataset: dict, application_profile: str):
    template_location = get_application_profile_location(application_profile)
    logger.debug(f'template location {template_location}')
    copytree(template_location, temp_dir, dirs_exist_ok=True)

    with open(Path(temp_dir) / 'config.json', 'w') as config_file:
        config_content = generate_report_builder_config(template_location, dataset)
        config_file.write(dumps(config_content))

    report_builder = ReportBuilder(target_path=temp_dir)
    report_builder.make_document()

    return Path(str(temp_dir)) / 'output/main.html'


def build_report_location(dataset_name: str, application_profile: str) -> str:
    return str(Path(RDF_DIFFER_REPORTS_DB) / f'{dataset_name}/{application_profile}')


def retrieve_report(dataset_name: str, application_profile: str) -> str:
    return str(next(Path(build_report_location(dataset_name, application_profile)).iterdir()))


def report_exists(dataset_name: str, application_profile: str) -> bool:
    report_location = build_report_location(dataset_name, application_profile)
    return dir_exists(report_location) and not dir_is_empty(report_location)


def save_report(report: str, dataset_name: str, application_profile: str) -> None:
    location_to_save = build_report_location(dataset_name, application_profile)

    if not dir_exists(location_to_save):
        Path(location_to_save).mkdir(parents=True)

    if not dir_is_empty(location_to_save):
        logger.debug(f'{location_to_save} is not empty. Removing existing content.')
        empty_directory(location_to_save)

    copy_file_to_destination(report, location_to_save)

    return