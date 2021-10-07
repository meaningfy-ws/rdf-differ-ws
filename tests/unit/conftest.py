import pathlib
from pathlib import Path

import pytest
from tests.unit import TEST_DATA


@pytest.fixture
def sample_ap_root_folder():
    return TEST_DATA / "sample_ap_config"


@pytest.fixture
def unexistent_ap_folder():
    return pathlib.Path("this/path/exists/not")
