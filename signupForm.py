from wtforms import TextField, PasswordField, validators, HiddenField, Form
from wtforms import TextAreaField, BooleanField
from wtforms.validators import Required, EqualTo, Optional
from wtforms.validators import Length, Email


class SignupForm(Form):
    email = TextField('Email address', validators=[
               Required('Please provide a valid email address'),
               Length(min=6, message=(u'Email address too short')),
               Email(message=(u'That\'s not a valid email address.'))])
       password = PasswordField('Pick a secure password', validators=[
               Required(),
               Length(min=6, message=(u'Please give a longer password'))])
       username = TextField('Choose your username', validators=[Required()])
       agree = BooleanField('I agree all your Terms of Services',
               validators=[Required(u'You must accept our Terms of Service')])
