from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class ConversationFlowForm(FlaskForm):
    name = StringField('Flow Name', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_active = BooleanField('Active', default=True)
    
    # Basic flow structure fields
    intro_text = TextAreaField('Introduction Text', validators=[DataRequired(), Length(max=1000)])
    talking_point_1 = TextAreaField('Talking Point 1', validators=[DataRequired(), Length(max=1000)])
    positive_reply_1 = TextAreaField('Positive Reply 1', validators=[DataRequired(), Length(max=1000)])
    neutral_reply_1 = TextAreaField('Neutral Reply 1', validators=[DataRequired(), Length(max=1000)])
    negative_reply_1 = TextAreaField('Negative Reply 1', validators=[DataRequired(), Length(max=1000)])
    outro_text = TextAreaField('Outro Text', validators=[DataRequired(), Length(max=1000)])
    
    submit = SubmitField('Save Conversation Flow')
