from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DateTimeLocalField, IntegerField, PasswordField, SelectField, SelectMultipleField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp


class ShootForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    location = SelectField("Location", choices=[("HALL", "Hall"), ("MEADOW", "Meadow"), ("WOODS", "Woods")], validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    attendees = SelectMultipleField("Attendees", coerce=int, validators=[Optional()])


class NewsForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=5)])
    summary = TextAreaField("Summary", validators=[Optional()])
    content = TextAreaField("Content", validators=[DataRequired(), Length(min=20)])
    published = BooleanField("Published", default=False)


class EventForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=5)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=1)])
    start_date = DateTimeLocalField("Start Date", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    location = StringField("Location", validators=[Optional()])
    published = BooleanField("Published", default=False)


class CreateMemberForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[Optional()])
    password = PasswordField("Password", validators=[Optional()])
    is_admin = BooleanField("Is Admin", default=False)
    create_membership = BooleanField("Create Membership", default=False)


class EditMemberForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[Optional()])
    password = PasswordField("Password", validators=[Optional()])
    is_admin = BooleanField("Is Admin", default=False)
    is_active = BooleanField("Is Active", default=True)
    membership_start_date = DateField("Membership Start Date", validators=[Optional()])
    membership_expiry_date = DateField("Membership Expiry Date", validators=[Optional()])
    membership_credits = IntegerField("Membership Credits", validators=[Optional()])
