import logging
import os

from rdf_differ.config import RDF_DIFFER_LOGGER, RDF_DIFFER_REPORT_TEMPLATE_LOCATION, \
    RDF_DIFFER_APPLICATION_PROFILES_LIST, TEMPLATES_FOLDER_PATH

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def validate_choice(choice, accepted_values):
    if choice not in accepted_values:
        exception_text = f"The choice {choice} is not valid. Accepted values:" \
                         f" {', '.join(accepted_values)}"
        logger.exception(exception_text)
        return False, exception_text
    return True, ''


def get_application_profile_location(application_profile):
    return f'{RDF_DIFFER_REPORT_TEMPLATE_LOCATION}/{application_profile}'


def get_template_types_for_an_application_profile(application_profile):
    valid_application_profile, exception_text = validate_choice(application_profile,
                                                                RDF_DIFFER_APPLICATION_PROFILES_LIST)
    if valid_application_profile:
        application_profile_templates_path = TEMPLATES_FOLDER_PATH / application_profile / "templates"
        return [x for x in os.listdir(application_profile_templates_path) if
                os.path.isdir(os.path.join(application_profile_templates_path, x))]
    return []
