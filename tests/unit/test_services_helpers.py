from rdf_differ.services import list_folders_from_path, list_files_from_path


def test_list_folders_from_path(sample_ap_root_folder):
    folders = list_folders_from_path(sample_ap_root_folder)
    assert isinstance(folders, list)
    assert 'ap1', 'ap2' in folders


def test_list_folders_from_path(sample_ap_root_folder):
    files = list_files_from_path(sample_ap_root_folder / "ap1")
    assert isinstance(files, list)
    assert len(files) == 0

    files = list_files_from_path(sample_ap_root_folder / "ap1" / "queries")
    assert len(files) == 2
    assert "added_instance_concepts.rq" in files
