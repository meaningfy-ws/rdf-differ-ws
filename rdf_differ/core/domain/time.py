from datetime import datetime

from pytz import timezone

# Defaults mirror the project config (RDF_DIFFER_TIMEZONE / RDF_DIFFER_TIME_FORMAT).
# Kept here so this domain helper imports no upward layer (core.domain must not reach
# core.adapters via the root config) — callers inject the configured values.
DEFAULT_TIMEZONE = "Europe/Paris"
DEFAULT_TIME_FORMAT = "%d-%b-%YT%H:%M:%S"


def get_timestamp(
    timezone_name: str = DEFAULT_TIMEZONE, time_format: str = DEFAULT_TIME_FORMAT
) -> str:
    """
    Generate a string timestamp in the given timezone and format.
    :return: timestamp
    """
    return datetime.now(tz=timezone(timezone_name)).strftime(time_format)
