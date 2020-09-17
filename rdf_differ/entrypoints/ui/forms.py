#!/usr/bin/python3

# forms.py
# Date:  17/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Module description

"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, DataRequired


class DiffGet(FlaskForm):
    dataset = StringField('dataset name', validators=[DataRequired(), Length(min=2, max=50)])
    submit = SubmitField('Get diff')
