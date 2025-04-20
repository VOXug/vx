from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class CampaignForm(FlaskForm):
    name = StringField('Campaign Name', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    max_calls_per_day = IntegerField('Max Calls Per Day', validators=[
        DataRequired(),
        NumberRange(min=1, max=10000, message='Value must be between 1 and 10000')
    ], default=1000)
    max_calls_per_hour = IntegerField('Max Calls Per Hour', validators=[
        DataRequired(),
        NumberRange(min=1, max=1000, message='Value must be between 1 and 1000')
    ], default=100)
    retry_attempts = IntegerField('Retry Attempts', validators=[
        DataRequired(),
        NumberRange(min=0, max=10, message='Value must be between 0 and 10')
    ], default=3)
    retry_delay_minutes = IntegerField('Retry Delay (minutes)', validators=[
        DataRequired(),
        NumberRange(min=1, max=1440, message='Value must be between 1 and 1440')
    ], default=60)
    start_date = DateTimeField('Start Date', format='%Y-%m-%d %H:%M', validators=[Optional()])
    end_date = DateTimeField('End Date', format='%Y-%m-%d %H:%M', validators=[Optional()])
    conversation_flow_id = SelectField('Conversation Flow', coerce=int, validators=[DataRequired()])
    voter_list_id = SelectField('Voter List', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Campaign')
