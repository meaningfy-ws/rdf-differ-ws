"""Unit tests for the pure naming helpers in rdf_differ.core.domain.naming."""

import pytest

from rdf_differ.core.domain.naming import (
    build_secure_filename,
    build_unique_name,
    check_dataset_name_validity,
)


@pytest.mark.parametrize(
    "name, expected",
    [
        # Valid: word chars, digits, underscore, colon and hyphen.
        ("valid_name", True),
        ("UPPER123", True),
        ("a:b-c_d", True),
        ("x", True),
        # Invalid: spaces, dots, slashes, non-word/non-ascii chars.
        ("with space", False),
        ("dot.name", False),
        ("slash/name", False),
        ("name#1", False),
        ("café", False),
        # Invalid: empty string is rejected (the pattern requires at least one char).
        ("", False),
        # Invalid: a trailing newline is rejected (fullmatch, not match).
        ("good\n", False),
        # Invalid: an embedded newline followed by more text.
        ("good\nBAD", False),
    ],
)
def test_check_dataset_name_validity(name, expected):
    """A dataset name is valid only when every char is a word char, colon or hyphen."""
    assert check_dataset_name_validity(name) is expected


def test_build_unique_name_appends_suffix_of_requested_length():
    """The generated name is the base plus a random suffix of the requested length."""
    base = "dataset"
    name = build_unique_name(base, length_added=8)

    assert name.startswith(base)
    assert len(name) == len(base) + 8


def test_build_unique_name_clamps_length_at_22():
    """A requested suffix length above 22 is clamped to 22."""
    base = "dataset"
    name = build_unique_name(base, length_added=30)

    assert name.startswith(base)
    assert len(name) == len(base) + 22


def test_build_unique_name_produces_distinct_names():
    """Two calls with the same base yield different unique names."""
    base = "dataset"

    assert build_unique_name(base) != build_unique_name(base)


def test_build_secure_filename_stays_under_location():
    """The result is placed under the given location directory."""
    location = "/tmp/uploads"

    result = build_secure_filename(location, "report.ttl")

    assert result.startswith(location + "/")


def test_build_secure_filename_neutralises_traversal():
    """A traversal filename is sanitised: no slashes or '..' survive in the leaf."""
    location = "/tmp/uploads"

    result = build_secure_filename(location, "../etc/passwd")
    leaf = result[len(location) + 1 :]

    assert "/" not in leaf
    assert ".." not in leaf
    # The leaf is prefixed with a uuid4 hex string (32 hex digits across 5 groups).
    uuid_prefix = leaf[:36]
    assert all(ch in "0123456789abcdef-" for ch in uuid_prefix)
    assert uuid_prefix.count("-") == 4
