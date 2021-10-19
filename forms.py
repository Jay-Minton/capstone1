from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import InputRequired, length

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), length(max=20)])
    email = StringField("Email", validators=[InputRequired(), length(max=50)])
    password = PasswordField("Password", validators=[InputRequired()])

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), length(max=20)])
    password = PasswordField("Password", validators=[InputRequired()])

class DeckForm(FlaskForm):
    invest_name = SelectField("Pick Your investigator", validators=[InputRequired()])
    deck_name = StringField("Name Your Deck", validators=[InputRequired()])