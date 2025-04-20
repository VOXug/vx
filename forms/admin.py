from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from models import User

class APIConfigForm(FlaskForm):
    name = StringField('Configuration Name', validators=[DataRequired()])
    key = StringField('API Key Name', validators=[DataRequired()])
    value = StringField('API Key Value', validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Configuration')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        Optional(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        EqualTo('password', message='Passwords must match')
    ])
    is_admin = BooleanField('Administrator', default=False)
    submit = SubmitField('Save User')
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_username = kwargs.get('obj', None).username if kwargs.get('obj', None) else None
        self.original_email = kwargs.get('obj', None).email if kwargs.get('obj', None) else None
    
    def validate_username(self, username):
        if self.original_username and self.original_username == username.data:
            return
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already taken. Please use a different username.')
    
    def validate_email(self, email):
        if self.original_email and self.original_email == email.data:
            return
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different email address.')
