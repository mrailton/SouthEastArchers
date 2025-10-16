from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, DateTimeField, BooleanField, IntegerField, FloatField, SelectField, DateField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange
from wtforms.widgets import CheckboxInput, ListWidget
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone', validators=[Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class NewsForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    published = BooleanField('Published')

class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    event_date = DateTimeField('Event Date', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    location = StringField('Location', validators=[Length(max=200)])
    published = BooleanField('Published')

class CreditPurchaseForm(FlaskForm):
    credits = IntegerField('Number of Credits', validators=[DataRequired(), NumberRange(min=1, max=100)])

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class ShootingNightForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    location = SelectField('Location', validators=[DataRequired()], 
                          choices=[('Hall', 'Hall'), ('Meadow', 'Meadow'), ('Woods', 'Woods')])
    attendees = MultiCheckboxField('Attendees', coerce=int)
    notes = TextAreaField('Notes', validators=[Length(max=500)])
