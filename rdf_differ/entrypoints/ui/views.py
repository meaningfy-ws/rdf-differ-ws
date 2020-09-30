#!/usr/bin/python3

# views.py
# Date:  17/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
UI pages

"""
from flask import render_template, redirect, flash, url_for

from rdf_differ.entrypoints.ui import app
from rdf_differ.entrypoints.ui.api_wrapper import get_datasets, create_diff as api_create_diff, get_dataset
from rdf_differ.entrypoints.ui.forms import CreateDiffForm


@app.route('/')
def index():
    """
    Home page containing the list of available dataset diffs.
    """
    datasets, _ = get_datasets()
    return render_template('index.html', datasets=datasets)


@app.route('/create-diff', methods=['GET', 'POST'])
def create_diff():
    """
    Page for creating a new dataset diff.
    """
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

        if status == 200:
            flash(response, 'success')
        else:
            flash(response, 'error')

        return redirect(url_for('view_dataset', dataset_id=form.dataset_name.data))

    return render_template('dataset/create_diff.html', title='Create diff', form=form)


@app.route('/diffs/<dataset_id>')
def view_dataset(dataset_id):
    """
    Page for viewing a dataset diff.
    :param dataset_id: The dataset identifier. This should be short alphanumeric string uniquely identifying the dataset
    """
    dataset, _ = get_dataset(dataset_id)
    return render_template('dataset/view_dataset.html', title=f'{dataset_id} view', dataset=dataset)
