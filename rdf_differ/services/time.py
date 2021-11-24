from datetime import datetime

from pytz import timezone

from rdf_differ import config


def get_timestamp() -> str:
    """
    generate a string timestamp based on the project's time format
    :return: timestamp
    """
    return datetime.now(tz=timezone(config.RDF_DIFFER_TIMEZONE)).strftime(config.RDF_DIFFER_TIME_FORMAT)
