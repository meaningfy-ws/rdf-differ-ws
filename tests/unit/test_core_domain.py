"""Unit tests for shared core domain helpers: strtobool, mime-type mapping, timestamps."""

from datetime import datetime

import pytest

from rdf_differ.core.domain import strtobool
from rdf_differ.core.domain.constants import (
    DEFAULT_INPUT_MIME_TYPE,
    DeltaOp,
    mime_type_for,
)
from rdf_differ.core.domain.time import get_timestamp


@pytest.mark.parametrize(
    "value",
    ["1", "true", "True", "TRUE", "yes", " y ", "on", "t"],
)
def test_strtobool_truthy_values(value):
    """Recognised truthy strings parse to True, case-insensitively and whitespace-stripped."""
    assert strtobool(value) is True


@pytest.mark.parametrize(
    "value",
    ["0", "false", "no", "n", "off", "f", "", "2", "random"],
)
def test_strtobool_falsy_values(value):
    """Anything outside the recognised truthy set parses to False."""
    assert strtobool(value) is False


@pytest.mark.parametrize(
    "file_name, expected",
    [
        ("ontology.ttl", "text/turtle"),
        ("ontology.rdf", "application/rdf+xml"),
        # Extension matching is case-insensitive.
        ("ONTOLOGY.TTL", "text/turtle"),
        ("ontology.RDF", "application/rdf+xml"),
    ],
)
def test_mime_type_for_known_extensions(file_name, expected):
    """A known extension maps to its declared RDF MIME type, ignoring case."""
    assert mime_type_for(file_name) == expected


@pytest.mark.parametrize(
    "file_name",
    ["data.unknownext", "no_extension"],
)
def test_mime_type_for_falls_back_to_turtle(file_name):
    """An unknown or missing extension falls back to the Turtle default."""
    assert mime_type_for(file_name) == DEFAULT_INPUT_MIME_TYPE
    assert DEFAULT_INPUT_MIME_TYPE == "text/turtle"


def test_delta_op_members():
    """DeltaOp exposes the two delta components as string-valued enum members."""
    assert DeltaOp.INSERTIONS == "insertions"
    assert DeltaOp.DELETIONS == "deletions"


def test_get_timestamp_returns_string():
    """get_timestamp returns a string."""
    assert isinstance(get_timestamp("Europe/Paris", "%Y"), str)


def test_get_timestamp_year_format_is_four_digits():
    """With a '%Y' format the timestamp is a 4-digit year."""
    result = get_timestamp("Europe/Paris", "%Y")

    assert len(result) == 4
    assert result.isdigit()


def test_get_timestamp_is_parseable_with_its_format():
    """The output is parseable back with datetime.strptime using the same format."""
    time_format = "%d-%b-%YT%H:%M:%S"
    result = get_timestamp("Europe/Paris", time_format)

    # Should not raise: the produced string round-trips through the given format.
    datetime.strptime(result, time_format)
