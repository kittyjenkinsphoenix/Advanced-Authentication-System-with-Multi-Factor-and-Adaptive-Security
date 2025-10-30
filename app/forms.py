from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
    CSRF = True  
    RecaptchaField = None
    #LoginForm should optionally include a RecaptchaField (but only render it after 3 failures—controlled in the route/template).

class MFASetupForm(FlaskForm):
    submit = SubmitField('Enable MFA')

class MFAVerifyForm(FlaskForm):
    totpCode = StringField('Authentication Code', validators=[DataRequired()])
    submit = SubmitField('Verify')

class LogoutForm(FlaskForm):
    submit = SubmitField('Logout')
    CSRF = True
