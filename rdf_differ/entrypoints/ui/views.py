#!/usr/bin/python3

# views.py
# Date:  17/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Module description

"""

from flask import render_template, redirect

from rdf_differ.entrypoints.ui import app
from rdf_differ.entrypoints.ui.forms import DiffGet


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/diffs', methods=['GET', 'POST'])
def diff_upload():
    form = DiffGet()
    if form.validate_on_submit():
        return redirect('/index')
    return render_template('diff_get.html', title='Get Diff', form=form)
