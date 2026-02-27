from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DateTimeLocalField,
    DecimalField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional


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
    roles = SelectMultipleField("Roles", coerce=int, validators=[Optional()])
    create_membership = BooleanField("Create Membership", default=False)


class EditMemberForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[Optional()])
    qualification = SelectField(
        "Qualification",
        choices=[
            ("none", "None"),
            ("beginner", "Beginner Course Completed"),
            ("ai", "Archery Ireland Member"),
            ("ifaf", "Irish Field Archery Federation Member"),
        ],
        validators=[DataRequired()],
    )
    qualification_detail = StringField("Qualification Detail", validators=[Optional()])
    password = PasswordField("Password", validators=[Optional()])
    roles = SelectMultipleField("Roles", coerce=int, validators=[Optional()])
    is_active = BooleanField("Is Active", default=True)
    membership_start_date = DateField("Membership Start Date", validators=[Optional()])
    membership_expiry_date = DateField("Membership Expiry Date", validators=[Optional()])
    membership_initial_credits = IntegerField("Initial Credits", validators=[Optional()])
    membership_purchased_credits = IntegerField("Purchased Credits", validators=[Optional()])


class SettingsForm(FlaskForm):
    """Form for managing application settings."""

    # Membership year start settings
    membership_year_start_month = IntegerField(
        "Membership Year Start Month", validators=[DataRequired(), NumberRange(min=1, max=12)], description="Month when membership year starts (1-12)"
    )
    membership_year_start_day = IntegerField(
        "Membership Year Start Day", validators=[DataRequired(), NumberRange(min=1, max=31)], description="Day when membership year starts (1-31)"
    )

    # Pricing settings (in euros, will be converted to cents)
    annual_membership_cost = IntegerField(
        "Annual Membership Cost (€)", validators=[DataRequired(), NumberRange(min=0)], description="Cost in euros (e.g., 100 for €100)"
    )
    membership_shoots_included = IntegerField(
        "Shoots Included", validators=[DataRequired(), NumberRange(min=0)], description="Number of shoots included with membership"
    )
    additional_shoot_cost = IntegerField(
        "Additional Shoot Cost (€)", validators=[DataRequired(), NumberRange(min=0)], description="Cost per additional shoot in euros"
    )

    # Cash payment settings
    cash_payment_instructions = TextAreaField(
        "Cash Payment Instructions",
        validators=[DataRequired(), Length(min=10, max=1000)],
        description="Instructions shown to users when they select cash payment",
    )

    # Feature toggles
    news_enabled = BooleanField("Enable News", default=False)
    events_enabled = BooleanField("Enable Events", default=False)


class RoleForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=255)])
    permissions = SelectMultipleField("Permissions", coerce=int, validators=[Optional()])


class ExpenseForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    amount = DecimalField("Amount (€)", places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    category = SelectField(
        "Category",
        choices=[
            ("equipment", "Equipment"),
            ("venue_hire", "Venue Hire"),
            ("insurance", "Insurance"),
            ("supplies", "Supplies"),
            ("maintenance", "Maintenance"),
            ("travel", "Travel"),
            ("affiliation_fees", "Affiliation Fees"),
            ("coaching", "Coaching"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=3)])
    receipt_reference = StringField("Receipt Reference", validators=[Optional(), Length(max=255)])


class IncomeForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    amount = DecimalField("Amount (€)", places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    category = SelectField(
        "Category",
        choices=[
            ("membership_fees", "Membership Fees"),
            ("shoot_fees", "Shoot Fees"),
            ("equipment_sales", "Equipment Sales"),
            ("donations", "Donations"),
            ("sponsorship", "Sponsorship"),
            ("grants", "Grants"),
            ("fundraising", "Fundraising"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=3)])
    source = StringField("Source", validators=[Optional(), Length(max=255)])


class FinancialStatementForm(FlaskForm):
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
