import json
import logging
from pathlib import Path
from shutil import copytree

from eds4jinja2.builders.report_builder import ReportBuilder

from rdf_differ.config import RDF_DIFFER_LOGGER
from utils.file_utils import dir_is_empty, empty_directory, copy_file_to_destination, dir_exists

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def build_report(temp_dir: str, template_location: str, query_files: dict, dataset: dict):
    additional_config = {"conf": {"query_files": query_files,
                                  "default_endpoint": dataset['query_url']}}
    logger.debug(f'template location {template_location}')

    copytree(template_location, temp_dir, dirs_exist_ok=True)

    with open(Path(temp_dir) / 'config.json', 'r') as config_file:
        config_content = json.load(config_file)

    logger.debug(f'template file {config_content["template"]}')

    report_builder = ReportBuilder(target_path=temp_dir, additional_config=additional_config)
    report_builder.make_document()
    return Path(str(temp_dir)) / f'output/{config_content["template"]}'


def build_report_location(dataset_name: str, application_profile: str, db_location: str) -> str:
    return str(Path(db_location) / f'{dataset_name}/{application_profile}')


def retrieve_report(dataset_name: str, application_profile: str, db_location: str) -> str:
    return str(next(Path(build_report_location(dataset_name, application_profile, db_location)).iterdir(), ''))


def report_exists(dataset_name: str, application_profile: str, db_location: str) -> bool:
    report_location = build_report_location(dataset_name, application_profile, db_location)
    return dir_exists(report_location) and not dir_is_empty(report_location)


def save_report(report: str, dataset_name: str, application_profile: str, db_location: str) -> None:
    location_to_save = build_report_location(dataset_name, application_profile, db_location)

    if not dir_exists(location_to_save):
        Path(location_to_save).mkdir(parents=True)

    if not dir_is_empty(location_to_save):
        logger.debug(f'{location_to_save} is not empty. Removing existing content.')
        empty_directory(location_to_save)

    logger.debug(f'{location_to_save}.')
    copy_file_to_destination(report, location_to_save)
