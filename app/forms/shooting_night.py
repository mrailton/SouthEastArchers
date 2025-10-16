from flask_wtf import FlaskForm
from wtforms import TextAreaField, DateField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length
from wtforms.widgets import CheckboxInput, ListWidget


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class ShootingNightForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    location = SelectField('Location', validators=[DataRequired()], 
                          choices=[('Hall', 'Hall'), ('Meadow', 'Meadow'), ('Woods', 'Woods')])
    attendees = MultiCheckboxField('Attendees', coerce=int)
    notes = TextAreaField('Notes', validators=[Length(max=500)])
