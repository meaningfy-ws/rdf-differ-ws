import json
import logging
import shutil
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


def build_dataset_reports_location(dataset_name: str, db_location: str) -> str:
    """
    build path for report location of given dataset

    :param dataset_name: dataset name
    :param db_location: which file system location to use to perform the action
    :return:
    """
    return str(Path(db_location) / dataset_name)


def build_report_location(dataset_name: str, application_profile: str, template_type: str, db_location: str) -> str:
    """
    build report path

    :param dataset_name: dataset name
    :param application_profile: application profile for report identification
    :param template_type: template to retrieve existence
    :param db_location: which file system location to use to perform the action
    :return: report location
    """
    return str(
        Path(build_dataset_reports_location(dataset_name, db_location)) / f'{application_profile}/{template_type}')


def retrieve_report(dataset_name: str, application_profile: str, template_type: str, db_location: str) -> str:
    """
    retrieve report path

    :param dataset_name: dataset name
    :param application_profile: application profile for report identification
    :param template_type: template to retrieve existence
    :param db_location: which file system location to use to perform the action
    :return:
    """
    return str(
        next(Path(build_report_location(dataset_name, application_profile, template_type, db_location)).iterdir(), ''))


def report_exists(dataset_name: str, application_profile: str, template_type: str, db_location: str) -> bool:
    """

    :param dataset_name: dataset name
    :param application_profile: application profile for report identification
    :param template_type: template to check existence
    :param db_location: which file system location to use to perform the action
    :return: if report exists return true otherwise false
    """
    report_location = build_report_location(dataset_name, application_profile, template_type, db_location)
    return dir_exists(report_location) and not dir_is_empty(report_location)


def get_all_reports(dataset_name: str, db_location: str) -> list:
    """
    Get all built reports for specified dataset
    :param dataset_name: dataset name
    :param db_location: which file system location to use to perform the action
    :return: list of application profiles and their variations
    """
    reports_location = Path(build_dataset_reports_location(dataset_name, db_location))
    if dir_exists(reports_location):
        reports = list()
        for ap_location in Path(reports_location).iterdir():
            reports.append(
                {
                    'application_profile': ap_location.name,
                    'template_variations': [location.name for location in ap_location.iterdir()]
                }
            )
        return reports

    return list()


def save_report(report: str, dataset_name: str, application_profile: str, template_type: str, db_location: str) -> None:
    """
    save report to specified location

    :param report: report to save
    :param dataset_name: dataset name
    :param application_profile: application profile for report identification
    :param template_type: template to save
    :param db_location: which file system location to use to perform the action
    """
    location_to_save = build_report_location(dataset_name, application_profile, template_type, db_location)

    if not dir_exists(location_to_save):
        Path(location_to_save).mkdir(parents=True)

    if not dir_is_empty(location_to_save):
        logger.debug(f'{location_to_save} is not empty. Removing existing content.')
        empty_directory(location_to_save)

    logger.debug(f'{location_to_save}.')
    copy_file_to_destination(report, location_to_save)


def remove_report(dataset_name: str, application_profile: str, template_type: str, db_location: str) -> bool:
    """
    remove report

    :param dataset_name: dataset name
    :param application_profile: application profile for report identification
    :param template_type: template to remove
    :param db_location: which file system location to use to perform the action
    :return: if report successfully deleted return true otherwise return false
    """
    report_location = build_report_location(dataset_name, application_profile, template_type, db_location)
    try:
        shutil.rmtree(report_location)
        return True
    except FileNotFoundError as e:
        logger.debug(
            f'no report found for {dataset_name} with {application_profile}, {template_type}. nothing to delete.')

    return False


def remove_all_reports(dataset_name: str, db_location: str) -> bool:
    """
    remove all reports for specified dataset

    :param dataset_name: dataset name
    :param db_location: which file system location to use to perform the action
    :return: if reports successfully deleted return true otherwise return false
    """
    report_location = build_dataset_reports_location(dataset_name, db_location)
    try:
        shutil.rmtree(report_location)
        return True
    except OSError as e:
        logger.debug(f'no reports found for {dataset_name}. nothing to delete.')

    return False
