"""Form input validation for the UI.

Pydantic models replace Flask-WTF. Routes parse the submitted form into these models;
a ``ValidationError`` is rendered back onto the form as field messages.
"""

import re

from pydantic import BaseModel, field_validator

_NAME_PATTERN = re.compile(r"^[\w\d_:-]+$")


class CreateDiffInput(BaseModel):
    """Validated fields of the create-diff form (files are handled by the route)."""

    dataset_name: str
    dataset_uri: str
    old_version_id: str = "old"
    new_version_id: str = "new"
    dataset_description: str = ""

    @field_validator("dataset_name")
    @classmethod
    def _valid_name(cls, value: str) -> str:
        value = value.strip()
        if not 2 <= len(value) <= 50:
            raise ValueError("Dataset name must be between 2 and 50 characters")
        if not _NAME_PATTERN.match(value):
            raise ValueError("Dataset name can contain only letters, numbers, _, :, and -")
        return value

    @field_validator("dataset_uri")
    @classmethod
    def _valid_uri(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("Dataset URI must be a valid URL")
        return value

    @field_validator("old_version_id", "new_version_id")
    @classmethod
    def _required_version(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Version name is required")
        return value
