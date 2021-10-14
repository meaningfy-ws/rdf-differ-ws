from pathlib import Path

from rdf_differ.services.report_handling import build_report_location, retrieve_report, report_exists, save_report


def test_build_report_location():
    dataset_name = 'dataset'
    application_profile = 'application_profile'
    db_location = '/db'
    expected_result = '/db/dataset/application_profile'

    report_location = build_report_location(dataset_name, application_profile, db_location)

    assert report_location == expected_result


def test_retrieve_report(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'

    db_location = tmpdir.mkdir('db')
    expected_result = db_location.mkdir(dataset_name).mkdir(application_profile).join('report.html')
    expected_result.write('data')

    report_location = retrieve_report(dataset_name, application_profile, db_location)

    assert str(report_location) == str(expected_result)


def test_report_exists_true(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'

    db_location = tmpdir.mkdir('db')
    report = db_location.mkdir(dataset_name).mkdir(application_profile).join('report.html')
    report.write('data')

    exists = report_exists(dataset_name, application_profile, db_location)

    assert exists is True


def test_report_exists_false(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'

    db_location = tmpdir.mkdir('db')

    exists = report_exists(dataset_name, application_profile, db_location)

    assert exists is False


def test_save_report(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'

    report = tmpdir.join('report.html')
    report.write('data')

    db_location = tmpdir.mkdir('db')

    save_report(report, dataset_name, application_profile, db_location)

    assert (Path(db_location) / 'dataset/application/report.html').read_text() == 'data'


def test_save_report_rewrite(tmpdir):
    dataset_name = 'dataset'
    application_profile = 'application'

    report = tmpdir.join('report.html')
    report.write('data')

    db_location = tmpdir.mkdir('db')
    old_report = db_location.mkdir(dataset_name).mkdir(application_profile).join('report.html')
    old_report.write('old data')

    save_report(report, dataset_name, application_profile, db_location)

    assert (Path(db_location) / 'dataset/application/report.html').read_text() == 'data'
