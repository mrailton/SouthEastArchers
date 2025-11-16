from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Optional, Length
from flask_wtf import FlaskForm


class ProfileForm(FlaskForm):
    """Member profile form"""
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2)])
    phone = StringField('Phone', validators=[Optional()])
    submit = SubmitField('Update Profile')
