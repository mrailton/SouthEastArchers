from flask_wtf import FlaskForm
from wtforms import DateField, PasswordField, RadioField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class SignupForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone (optional)", validators=[Optional()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    password_confirm = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    payment_method = RadioField(
        "Payment Method",
        choices=[("cash", "Cash"), ("online", "Online Payment")],
        validators=[DataRequired()],
        default="online",
    )
    submit = SubmitField("Create Account")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")
