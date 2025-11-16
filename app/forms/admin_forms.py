from wtforms import StringField, TextAreaField, IntegerField, SubmitField, DateTimeField
from wtforms.validators import DataRequired, Optional, Length
from flask_wtf import FlaskForm


class ShootingNightForm(FlaskForm):
    """Create/edit shooting night form"""
    location = StringField('Location', validators=[DataRequired(), Length(min=2)])
    date = DateTimeField('Date & Time', validators=[DataRequired()])
    capacity = IntegerField('Capacity', default=30)
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Create')


class NewsForm(FlaskForm):
    """Create/edit news form"""
    title = StringField('Title', validators=[DataRequired(), Length(min=5)])
    summary = StringField('Summary', validators=[Optional()])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=20)])
    submit = SubmitField('Create')


class EventForm(FlaskForm):
    """Create/edit event form"""
    title = StringField('Title', validators=[DataRequired(), Length(min=5)])
    description = TextAreaField('Description', validators=[DataRequired()])
    start_date = DateTimeField('Start Date', validators=[DataRequired()])
    location = StringField('Location', validators=[Optional()])
    submit = SubmitField('Create')
