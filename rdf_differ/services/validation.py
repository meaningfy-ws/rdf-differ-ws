import logging

from rdf_differ.config import RDF_DIFFER_LOGGER

logger = logging.getLogger(RDF_DIFFER_LOGGER)


def validate_choice(choice, accepted_values):
    if choice not in accepted_values:
        exception_text = f"The choice f{choice} is not valid. Accepted values:" \
                         f" {', '.join(accepted_values)}"
        logger.exception(exception_text)
        return False, exception_text
    return True, ''
