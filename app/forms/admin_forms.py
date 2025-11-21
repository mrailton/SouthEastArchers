from wtforms import (
    StringField,
    TextAreaField,
    IntegerField,
    SubmitField,
    DateField,
    SelectField,
    SelectMultipleField,
)
from wtforms.validators import DataRequired, Optional, Length
from flask_wtf import FlaskForm


class ShootForm(FlaskForm):
    """Create/edit shoot form"""

    date = DateField("Date", validators=[DataRequired()])
    location = SelectField(
        "Location",
        choices=[("HALL", "Hall"), ("MEADOW", "Meadow"), ("WOODS", "Woods")],
        validators=[DataRequired()],
    )
    description = TextAreaField("Description", validators=[Optional()])
    attendees = SelectMultipleField("Attendees", coerce=int, validators=[Optional()])
    submit = SubmitField("Create Shoot")


class NewsForm(FlaskForm):
    """Create/edit news form"""

    title = StringField("Title", validators=[DataRequired(), Length(min=5)])
    summary = StringField("Summary", validators=[Optional()])
    content = TextAreaField("Content", validators=[DataRequired(), Length(min=20)])
    submit = SubmitField("Create")


class EventForm(FlaskForm):
    """Create/edit event form"""

    title = StringField("Title", validators=[DataRequired(), Length(min=5)])
    description = TextAreaField("Description", validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()])
    location = StringField("Location", validators=[Optional()])
    submit = SubmitField("Create")
