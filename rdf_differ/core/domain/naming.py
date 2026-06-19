"""Pure naming and identifier helpers (domain layer).

Relocated here from the legacy ``rdf_differ.utils.file_utils`` during the utils
dissolution (DEC-7). These are pure functions: dataset-name validation, unique-name
generation, and secure-filename construction. They perform no filesystem I/O —
``build_secure_filename`` only sanitises and composes a path string via
``werkzeug.utils.secure_filename`` and a UUID, so it remains domain-pure.
"""

import logging
import re
from pathlib import Path
from uuid import uuid4

import shortuuid
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


def check_dataset_name_validity(name: str) -> bool:
    return bool(re.match(r"^[\w\d_:-]*$", name, flags=re.A))


def build_unique_name(base: str, length_added: int = 8) -> str:
    if length_added > 22:
        logger.warning("currently max accepted length_added is 22")
        length_added = 22

    return f"{base}{shortuuid.uuid()[:length_added]}"


def build_secure_filename(location: str, filename: str) -> str:
    return str(Path(location) / (str(uuid4()) + secure_filename(filename)))
