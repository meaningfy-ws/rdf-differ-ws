#!/usr/bin/python3

# forms.py
# Date:  17/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
    Form classes to be used in views.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired
from wtforms import StringField, SubmitField, FileField, SelectField
from wtforms.validators import Length, DataRequired, URL, Regexp


class CreateDiffForm(FlaskForm):
    dataset_name = StringField('Dataset name', validators=[DataRequired(),
                                                           Regexp(r'^[\w\d_:-]*$',
                                                                  message='Dataset name can contain only letters, numbers, _, :, and -'),
                                                           Length(min=2, max=50)])
    dataset_description = StringField('Dataset description', description='Optional description of the dataset.')
    # TODO: find out if the URL validator is enough or we'll need to create a custom one for URIs
    dataset_uri = StringField('Dataset URI', validators=[DataRequired(), URL()])

    old_version_file_content = FileField('Old dataset file', validators=[FileRequired()])
    old_version_id = StringField('Old dataset version name', validators=[DataRequired()], default='old')
    new_version_file_content = FileField('New dataset file', validators=[FileRequired()])
    new_version_id = StringField('New dataset version name', validators=[DataRequired()], default='new')

    submit = SubmitField('Create diff')


class NonValidatingSelectMultipleField(SelectField):
    """
    Allow select fields to have dynamically set values
    """
    def pre_validate(self, form):
        pass


class BuildReportForm(FlaskForm):
    application_profile = NonValidatingSelectMultipleField('Application profile', choices=[])
    template_type = NonValidatingSelectMultipleField('Template type', choices=[])
    submit = SubmitField('Build report')
