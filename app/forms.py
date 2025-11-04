from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Optional
from app.models import User

# Define Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    recaptcha = RecaptchaField(validators=[Optional()])
    submit = SubmitField('Login')

# MFA Forms
class MFASetupForm(FlaskForm):
    submit = SubmitField('Enable MFA')

# MFA Verification Form
class MFAVerifyForm(FlaskForm):
    totpCode = StringField('Authentication Code', validators=[DataRequired()])
    submit = SubmitField('Verify')

# Logout Form
class LogoutForm(FlaskForm):
    submit = SubmitField('Logout')
    CSRF = True
