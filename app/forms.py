from flask_wtf import FlaskForm
from wtforms import (StringField,
                     SubmitField,
                     BooleanField,
                     PasswordField,
                     HiddenField,
                     SelectField,
                     IntegerField,
                     DateField)
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.models import User
from datetime import datetime


class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Submit')


class SetMacroForm(FlaskForm):
    PERCENT_CHOICES = [(.05, "5%"),
                       (.1, "10%"),
                       (.15, "15%"),
                       (.2, "20%"),
                       (.25, "25%"),
                       (.3, "30%"),
                       (.35, "35%"),
                       (.4, "40%"),
                       (.45, "45%"),
                       (.5, "50%"),
                       (.55, "55%"),
                       (.6, "60%"),
                       (.65, "65%"),
                       (.7, "70%"),
                       (.75, "75%"),
                       (.8, "80%"),
                       (.85, "85%"),
                       (.9, "90%")]

    calories = IntegerField('Calories', validators=[DataRequired()])
    protein = SelectField('Protein', choices=PERCENT_CHOICES, validators=[
        DataRequired()], default=.1)
    fat = SelectField('Fat', choices=PERCENT_CHOICES,
                      validators=[DataRequired()])
    carbs = SelectField('Carbs', choices=PERCENT_CHOICES,
                        validators=[DataRequired()])
    change_macros = SubmitField('Update')


class SetMacroGrams(FlaskForm):
    calories = IntegerField('Calories', validators=[DataRequired()])
    protein = IntegerField('Protein', validators=[DataRequired()])
    fat = IntegerField('Fat', validators=[DataRequired()])
    carbs = IntegerField('Carbs', validators=[DataRequired()])
    change_macros = SubmitField('Update')


 
    MEAL_OPTIONS = [('Breakfast', 'Breakfast'),
                    ('Lunch', 'Lunch'),
                    ('Dinner', 'Dinner'),
                    ('Snacks', 'Snacks')]
    dt = DateField('DatePicker', format='%B %d, %Y')
    meal_select = SelectField('Meal', choices=MEAL_OPTIONS, validators=[
        DataRequired()])


class QuickAddCals(FlaskForm):
    calories = IntegerField('Calories', validators=[DataRequired()])
    protein = IntegerField('Protein', validators=[DataRequired()])
    fat = IntegerField('Fat', validators=[DataRequired()])
    carbs = IntegerField('Carbs', validators=[DataRequired()])
    quick_add = SubmitField('Update')


class AddToDiaryForm(FlaskForm):
    MEAL_CHOICES = [("Breakfast", "Breakfast"), ("Lunch", "Lunch"),
                    ("Dinner", "Dinner"), ("Snacks", "Snacks")]
    add = SubmitField('Add')
    meal = SelectField(label='Select Meal',
                       choices=MEAL_CHOICES, validators=[DataRequired()])
    quantity = StringField(label='Quantity', validators=[DataRequired()])


class DiaryDatePicker(FlaskForm):
    date = StringField(default=datetime.utcnow().strftime(
        '%B %d, %Y'), validators=[DataRequired()])


class RemoveFood(FlaskForm):
    entry_id = HiddenField('', validators=[DataRequired()])


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
