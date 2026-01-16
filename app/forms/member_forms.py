from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TelField
from wtforms.validators import DataRequired, EqualTo, Length, Optional


class ProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2)])
    phone = TelField("Phone", validators=[Optional()])


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("new_password", message="New passwords do not match")])
