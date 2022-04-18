import uuid
from json import dumps
from pathlib import Path

from rdf_differ.services.report_handling import build_report_location, retrieve_report, report_exists, save_report, \
    build_dataset_reports_location, remove_all_reports, remove_report, build_report_name, generate_meta_file, \
    read_meta_file, find_dataset_name_by_id
from rdf_differ.utils.file_utils import dir_exists


def test_build_dataset_report_location():
    dataset_name = 'dataset'
    reports_location = '/reports'
    expected_result = '/reports/dataset'

    report_location = build_dataset_reports_location(dataset_name, reports_location)

    assert report_location == expected_result


def test_build_report_location():
    dataset_name = 'dataset'
    application_profile = 'application_profile'
    template_type = 'template_type'
    reports_location = '/reports'
    expected_result = '/reports/dataset/application_profile/template_type'

    report_location = build_report_location(dataset_name, application_profile, template_type, reports_location)

    assert report_location == expected_result


def test_build_report_name():
    dataset_name = 'dataset'
    application_profile = 'application_profile'
    template_type = 'template_type'
    timestamp = '12-12-2021T12:12:12'
    extension = 'html'
    destination_folder = '/db/dataset/application_profile/template_type/'
    expected_result = '/db/dataset/application_profile/template_type/dataset-application_profile-template_type-12-12-2021T12:12:12.html'

    report_location = build_report_name(destination_folder, dataset_name, application_profile, template_type, timestamp,
                                        extension)

    assert report_location == expected_result


def test_retrieve_report(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'
    template_type = 'template_type'

    db_location = tmpdir.mkdir('db')
    expected_result = db_location.mkdir(dataset_name).mkdir(application_profile).mkdir(template_type).join(
        'report.html')
    expected_result.write('data')

    report_location = retrieve_report(dataset_name, application_profile, template_type, db_location)

    assert str(report_location) == str(expected_result)


def test_report_exists_true(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'
    template_type = 'template_type'

    db_location = tmpdir.mkdir('db')
    expected_result = db_location.mkdir(dataset_name).mkdir(application_profile).mkdir(template_type).join(
        'report.html')
    expected_result.write('data')

    exists = report_exists(dataset_name, application_profile, template_type, db_location)

    assert exists is True


def test_report_exists_false(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'
    template_type = 'template_type'

    db_location = tmpdir.mkdir('db')

    exists = report_exists(dataset_name, application_profile, template_type, db_location)

    assert exists is False


def test_save_report(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'
    template_type = 'template_type'
    timestamp = '12-12-2021T12:12:12'

    report = tmpdir.join('report.html')
    report.write('data')

    db_location = tmpdir.mkdir('db')

    save_report(report, dataset_name, application_profile, template_type, timestamp, db_location)

    assert (Path(
        db_location) / f'dataset/application/template_type/{dataset_name}-{application_profile}-{template_type}-{timestamp}.html').read_text() == 'data'


def test_save_report_rewrite(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'
    template_type = 'template_type'
    timestamp = '12-12-2021T12:12:12'

    report = tmpdir.join('report.html')
    report.write('data')

    db_location = tmpdir.mkdir('db')
    old_report = db_location.mkdir(dataset_name).mkdir(application_profile).mkdir(template_type).join('report.html')
    old_report.write('old data')

    save_report(report, dataset_name, application_profile, template_type, timestamp, db_location)

    assert (Path(
        db_location) / f'dataset/application/template_type/{dataset_name}-{application_profile}-{template_type}-{timestamp}.html').read_text() == 'data'


def test_remove_all_reports_success(tmpdir):
    dataset_name = 'dataset'
    db_location = tmpdir.mkdir('db')
    report_location = db_location.mkdir(dataset_name)
    report_location.join('report.html')

    success = remove_all_reports(dataset_name, db_location)

    assert not dir_exists(report_location)
    assert success


def test_remove_all_reports_failure(tmpdir):
    dataset_name = 'dataset'
    db_location = tmpdir.mkdir('db')

    success = remove_all_reports(dataset_name, db_location)

    assert not success


def test_remove_report_success(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'
    template_type = 'template_type'

    db_location = tmpdir.mkdir('db')
    report_location = db_location.mkdir(dataset_name).mkdir(application_profile).mkdir(template_type)
    report_location.join('report.html')

    success = remove_report(dataset_name, application_profile, template_type, db_location)

    assert not dir_exists(report_location)
    assert success


def test_remove_report_failure(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'
    template_type = 'template_type'

    db_location = tmpdir.mkdir('db')

    assert not remove_report(dataset_name, application_profile, template_type, db_location)


def test_generate_meta_file_and_read_file(tmpdir):
    uid = str(uuid.uuid4())
    dataset_name = 'dataset'
    timestamp = '12-12-2012T12:12:12'
    report_base_location = tmpdir.mkdir(uid)

    meta_data = generate_meta_file(str(report_base_location), uid, dataset_name, timestamp)

    assert meta_data['uid'] == uid
    assert meta_data['dataset_name'] == dataset_name
    assert meta_data['created_at'] == timestamp

    meta_content = read_meta_file(str(report_base_location))

    assert meta_content['uid'] == uid
    assert meta_content['dataset_name'] == dataset_name
    assert meta_content['created_at'] == timestamp


def test_find_dataset_name_by_id(tmpdir):
    uid = str(uuid.uuid4())
    dataset_name = 'dataset'
    timestamp = '12-12-2012T12:12:12'
    reports_location = tmpdir.mkdir('reports')
    dataset_base_location = reports_location.mkdir(uid)
    meta_file = dataset_base_location.join('meta.json')
    meta_file.write(dumps({'dataset_name': dataset_name, 'created_at': timestamp, 'uid': uid}))

    dataset_name_found = find_dataset_name_by_id(uid, reports_location)
    assert dataset_name_found == dataset_name


def test_find_datast_name_by_id_failure(tmpdir):
    uid = str(uuid.uuid4())
    reports_location = tmpdir.mkdir('reports')

    assert not find_dataset_name_by_id(uid, reports_location)
