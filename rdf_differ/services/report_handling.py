import json
import logging
import shutil
from distutils.dir_util import copy_tree
from json import loads, dumps
from pathlib import Path

from eds4jinja2.builders.report_builder import ReportBuilder
from werkzeug.exceptions import UnprocessableEntity

from rdf_differ.config import RDF_DIFFER_LOGGER, RDF_DIFFER_REPORTS_DB, RDF_DIFFER_META_NAME
from rdf_differ.services.time import get_timestamp
from rdf_differ.utils.file_utils import dir_is_empty, empty_directory, copy_file_to_destination, dir_exists, \
    list_folder_paths_from_path

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def build_report(temp_dir: str, template_location: str, query_files: dict, application_profile: str, dataset_name: str,
                 dataset: dict,
                 timestamp: str):
    """
    :param temp_dir: location to temporarily save the report
    :param template_location: report location
    :param query_files: list of files to be included in the query
    :param application_profile: application profile for report identification
    :param dataset_name: dataset name
    :param dataset: data about dataset
    :param timestamp: time of report creation
    :return:
    """
    additional_config = {
        "conf": {
            "query_files": query_files,
            "default_endpoint": dataset['query_url'],
            "dataset_name": dataset_name,
            "application_profile": application_profile,
            "timestamp": timestamp
        }
    }
    logger.debug(f'template location {template_location}')

    copy_tree(template_location, temp_dir)

    try:
        with open(Path(temp_dir) / 'config.json', 'r') as config_file:
            config_content = json.load(config_file)

        logger.debug(f'template file {config_content["template"]}')
    except FileNotFoundError as e:
        logger.exception(str(e))
        raise UnprocessableEntity("config.json file is missing from the chosen template variant folder")

    report_builder = ReportBuilder(target_path=temp_dir, additional_config=additional_config)
    report_builder.make_document()
    return Path(str(temp_dir)) / f'output/{config_content["template"]}'


def build_dataset_reports_location(dataset_name: str, reports_location: str) -> str:
    """
    build path for report location of given dataset

    :param dataset_name: dataset name
    :param reports_location: which file system location to use to perform the action
    :return:
    """
    return str(Path(reports_location) / dataset_name)


def build_report_location(dataset_name: str, application_profile: str, template_type: str,
                          reports_location: str) -> str:
    """
    build report path

    :param dataset_name: dataset name
    :param application_profile: application profile for report identification
    :param template_type: template to retrieve existence
    :param reports_location: which file system location to use to perform the action
    :return: report location
    """
    return str(
        Path(build_dataset_reports_location(dataset_name, reports_location)) / f'{application_profile}/{template_type}')


def build_report_name(destination_folder: str, dataset_name: str, application_profile: str, template_type: str,
                      timestamp: str, extension: str) -> str:
    """
    build absolute report path including the filename

    :param destination_folder: report location
    :param dataset_name: dataset name
    :param application_profile: application profile for report identification
    :param template_type: template to retrieve existence
    :param timestamp: time of report creation
    :param extension: report extension
    :return: absolute report path
    """
    return str(
        Path(destination_folder) / f'{dataset_name}-{application_profile}-{template_type}-{timestamp}.{extension}')


def retrieve_report(dataset_name: str, application_profile: str, template_type: str, reports_location: str) -> str:
    """
    retrieve report path

    :param dataset_name: dataset name
    :param application_profile: application profile for report identification
    :param template_type: template to retrieve existence
    :param reports_location: which file system location to use to perform the action
    :return:
    """
    return str(
        next(Path(build_report_location(dataset_name, application_profile, template_type, reports_location)).iterdir(),
             ''))


def report_exists(dataset_name: str, application_profile: str, template_type: str, reports_location: str) -> bool:
    """

    :param dataset_name: dataset name
    :param application_profile: application profile for report identification
    :param template_type: template to check existence
    :param reports_location: which file system location to use to perform the action
    :return: if report exists return true otherwise false
    """
    report_location = build_report_location(dataset_name, application_profile, template_type, reports_location)
    return dir_exists(report_location) and not dir_is_empty(report_location)


def get_all_reports(dataset_name: str, reports_location_db: str) -> list:
    """
    Get all built reports for specified dataset
    :param dataset_name: dataset name
    :param reports_location_db: which file system location to use to perform the action
    :return: list of application profiles and their variations
    """
    reports_location = Path(build_dataset_reports_location(dataset_name, reports_location_db))
    if dir_exists(reports_location):
        reports = list()
        for ap_location in list_folder_paths_from_path(reports_location):
            reports.append(
                {
                    'application_profile': Path(ap_location).name,
                    'template_variations': [location.name for location in Path(ap_location).iterdir()]
                }
            )
        return reports

    return list()


def save_report(report: str, dataset_name: str, application_profile: str, template_type: str, timestamp: str,
                reports_location: str) -> None:
    """
    save report to specified location

    :param report: report to save
    :param dataset_name: dataset name
    :param application_profile: application profile for report identification
    :param template_type: template to save
    :param timestamp: time of report creation
    :param reports_location: which file system location to use to perform the action
    """
    report_extension = Path(report).suffix[1:]  # remove `.` from extension
    location_to_save = build_report_location(dataset_name, application_profile, template_type, reports_location)
    report_name = build_report_name(location_to_save, dataset_name, application_profile, template_type, timestamp,
                                    report_extension)

    if not dir_exists(location_to_save):
        Path(location_to_save).mkdir(parents=True)

    if not dir_is_empty(location_to_save):
        logger.debug(f'{location_to_save} is not empty. Removing existing content.')
        empty_directory(location_to_save)

    logger.debug(f'{location_to_save}.')
    copy_file_to_destination(report, report_name)


def remove_report(dataset_name: str, application_profile: str, template_type: str, reports_location: str) -> bool:
    """
    remove report

    :param dataset_name: dataset name
    :param application_profile: application profile for report identification
    :param template_type: template to remove
    :param reports_location: which file system location to use to perform the action
    :return: if report successfully deleted return true otherwise return false
    """
    report_location = build_report_location(dataset_name, application_profile, template_type, reports_location)
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


def generate_meta_file(reports_location: str, uid: str, dataset_name: str, timestamp: str = '') -> dict:
    """
    generate meta file for diff
    :param reports_location: location of diff reports
    :param uid: uid of dataset
    :param dataset_name: dataset name
    :param timestamp: time of diff creation
    :return: meta file
    """
    timestamp = timestamp or get_timestamp()
    meta_data = {
        'uid': uid,
        'dataset_name': dataset_name,
        'created_at': timestamp
    }
    meta_file = Path(reports_location) / RDF_DIFFER_META_NAME
    meta_file.write_text(dumps(meta_data))
    return meta_data


def read_meta_file(report_base_location: str, meta_file_name: str = 'meta.json') -> dict:
    """
    method to read data from meta file
    :param report_base_location: report location
    :param meta_file_name: custom meta name, defaults to "meta.json"
    :return: contents of the meta file
    """
    logger.debug(loads((Path(report_base_location) / meta_file_name).read_text()))
    return loads((Path(report_base_location) / meta_file_name).read_text())


def find_dataset_name_by_id(dataset_id: str, reports_location: str = RDF_DIFFER_REPORTS_DB) -> str:
    """
    method to search for dataset name based on the id
    :param dataset_id: uid of the dataset diff
    :param reports_location: which file system location to use to perform the action
    :return: location of reports
    """
    for location in list_folder_paths_from_path(Path(reports_location)):
        content = read_meta_file(Path(reports_location) / location)
        if content.get('uid', None) == dataset_id:
            return content.get('dataset_name')

    return ''
