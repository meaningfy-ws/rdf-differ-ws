#!/usr/bin/python3

# views.py
# Date:  17/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
UI pages
"""
import tempfile
from pathlib import Path

from flask import render_template, redirect, flash, url_for, send_from_directory, request

from rdf_differ.entrypoints.ui import app
from rdf_differ.entrypoints.ui.api_wrapper import get_datasets, create_diff as api_create_diff, get_dataset, get_report, \
    get_active_tasks as api_get_active_tasks, revoke_task as api_revoke_task, get_application_profiles, build_report
from rdf_differ.entrypoints.ui.forms import CreateDiffForm, BuildReportForm
from rdf_differ.entrypoints.ui.helpers import get_error_message_from_response

# this allows feeding the logs to gunicorn
logger = app.logger


@app.route('/')
def index():
    """
    Home page containing the list of available dataset diffs.
    """
    logger.debug('request index view')
    datasets, _ = get_datasets()

    logger.debug('render index view')
    return render_template('index.html', datasets=datasets)


@app.route('/create-diff', methods=['GET', 'POST'])
def create_diff():
    """
    Page for creating a new dataset diff.
    """
    logger.debug('request create diff view')

    form = CreateDiffForm()

    if form.validate_on_submit():
        response, status = api_create_diff(
            dataset_name=form.dataset_name.data,
            dataset_description=form.dataset_description.data,
            dataset_uri=form.dataset_uri.data,
            old_version_id=form.old_version_id.data,
            old_version_file=form.old_version_file_content.data,
            new_version_id=form.new_version_id.data,
            new_version_file=form.new_version_file_content.data
        )

        if status != 200:
            exception_text = get_error_message_from_response(response)
            logger.exception(exception_text)
            flash(exception_text, 'error')
        else:
            flash(response, 'success')
            logger.debug('render create diff view')
            return redirect(url_for('get_active_tasks'))

    logger.debug('render create diff clean view')
    return render_template('dataset/create_diff.html', title='Create diff', form=form)


@app.route('/diffs/<dataset_id>', methods=['GET', 'POST'])
def view_dataset(dataset_id: str):
    """
    Page for viewing a dataset diff.
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    """
    logger.debug(f'request dataset view for: {dataset_id}')

    dataset, _ = get_dataset(dataset_id)

    application_profiles, _ = get_application_profiles()
    form = BuildReportForm()
    try:
        form.application_profile.choices = [(item['application_profile'], item['application_profile']) for item in
                                            application_profiles]
        form.template_type.choices = [(item, item) for item in
                                      application_profiles[0]['template_variations']]
    except Exception as e:
        logger.exception(str(e))

    if request.method == 'POST':
        if form.validate_on_submit():
            response, status = build_report(
                dataset_id=dataset_id,
                application_profile=form.application_profile.data,
                template_type=form.template_type.data,
            )

            if status != 200:
                logger.exception(response)
                flash(response, 'error')
            else:
                flash('report started building', 'success')
                logger.debug(response)
                logger.debug('render create diff view')

        # this solves issues with reloading page with preselected application profile
        # which leads to wrong template variation assignments
        return redirect(url_for('view_dataset', dataset_id=dataset_id))

    logger.debug(f'render dataset view for: {dataset_id}')
    return render_template('dataset/view_dataset.html', title=f'{dataset_id} view',
                           dataset=dataset, form=form, application_profiles=application_profiles)


@app.route('/diff-report/<dataset_id>/<application_profile>/<template_type>')
def download_report(dataset_id: str, application_profile: str, template_type: str):
    logger.debug(f'request diff report view for: {dataset_id}')
    try:
        with tempfile.TemporaryDirectory() as temp_folder:
            report_content, extension, _ = get_report(dataset_id, application_profile, template_type)
            file_name = f"report-{dataset_id}-{application_profile}-{template_type}{extension}"
            logger.debug(file_name)
            report = Path(temp_folder) / file_name
            report.write_bytes(report_content)
            logger.debug(f'render diff report view for: {dataset_id}')
            return send_from_directory(Path(temp_folder), file_name, as_attachment=True)
    except Exception as e:
        logger.exception(str(e))

        flash(str(e), 'error')
        datasets, _ = get_datasets()

        logger.debug('redirect to index view')
        return render_template('index.html', datasets=datasets)


@app.route('/tasks')
def get_active_tasks():
    """
    Page containing the list of active tasks.
    """
    logger.debug('request active tasks view')
    tasks, _ = api_get_active_tasks()

    logger.debug(tasks)
    logger.debug('render active tasks view')
    return render_template('tasks/view_active_tasks.html', tasks=tasks)


@app.route('/revoke-task/<task_id>')
def revoke_task(task_id: str):
    """
    helper to revoke task from UI
    :param task_id: task to kill
    """
    logger.debug(f'request revoking for : {task_id}')
    message, status = api_revoke_task(task_id)
    if status == 200:
        flash(message, 'success')
    else:
        logger.exception(message)
        flash(message, 'error')

    return redirect(url_for('get_active_tasks'))
