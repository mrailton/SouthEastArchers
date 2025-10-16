from flask_wtf import FlaskForm
from wtforms import IntegerField
from wtforms.validators import DataRequired, NumberRange


class CreditPurchaseForm(FlaskForm):
    credits = IntegerField('Number of Credits', validators=[DataRequired(), NumberRange(min=1, max=100)])
