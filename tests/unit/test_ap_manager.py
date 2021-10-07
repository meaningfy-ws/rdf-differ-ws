import pathlib

import pytest
from werkzeug.exceptions import NotFound

from rdf_differ.services.ap_manager import ApplicationProfileManager


def test_ap_manager_creation(sample_ap_root_folder):
    apm = ApplicationProfileManager(root_folder=sample_ap_root_folder, application_profile="ap1", template_type="")
    assert apm is not None


def test_ap_manager_exception(unexistent_ap_folder):
    apm = ApplicationProfileManager(root_folder=unexistent_ap_folder, application_profile="ap1", template_type="")
    with pytest.raises(FileNotFoundError):
        apm.path_to_ap_folder()
    with pytest.raises(FileNotFoundError):
        apm.list_aps()


def test_list_functions_positive(sample_ap_root_folder):
    apm = ApplicationProfileManager(root_folder=sample_ap_root_folder, application_profile="ap1", template_type="html")
    assert isinstance(apm.path_to_ap_folder(), pathlib.Path)
    assert sample_ap_root_folder / "ap1" == apm.path_to_ap_folder()

    assert "ap1" in apm.list_aps()
    assert "ap2" in apm.list_aps()
    assert isinstance(apm.list_aps(), list)

    assert apm.queries_folder().is_dir()
    assert "ap1/queries" in str(apm.queries_folder())
    assert isinstance(apm.get_queries_dict(), dict)
    assert 'added_instance_concepts.rq' in apm.get_queries_dict().keys()
    assert str(apm.queries_folder() / 'added_instance_concepts.rq') in apm.get_queries_dict().values()

    assert "html" in apm.list_template_variants()
    assert "json" in apm.list_template_variants()

    assert "template_variants/html" in str(apm.template_folder())
    apm = ApplicationProfileManager(root_folder=sample_ap_root_folder, application_profile="ap1", template_type="json")
    assert "template_variants/json" in str(apm.template_folder())


def test_list_functions_negative(sample_ap_root_folder):
    apm = ApplicationProfileManager(root_folder=sample_ap_root_folder, application_profile="ap3", template_type="")

    with pytest.raises(LookupError):
        apm.queries_folder()

    apm = ApplicationProfileManager(root_folder=sample_ap_root_folder, application_profile="ap2", template_type="")
    with pytest.raises(FileNotFoundError):
        apm.queries_folder()

    apm = ApplicationProfileManager(root_folder=sample_ap_root_folder, application_profile="ap3", template_type="")
    with pytest.raises(NotFound):
        apm.list_template_variants()
    apm = ApplicationProfileManager(root_folder=sample_ap_root_folder, application_profile="ap1",
                                    template_type="xhtmlz")
    with pytest.raises(NotFound):
        apm.template_folder()

    apm = ApplicationProfileManager(root_folder=sample_ap_root_folder, application_profile="ap2",
                                    template_type="html")
    with pytest.raises(NotFound):
        apm.template_folder()
