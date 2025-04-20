from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from models import Language

class VoiceModelForm(FlaskForm):
    name = StringField('Model Name', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    voice_file = FileField('Voice Sample File', validators=[
        FileRequired(),
        FileAllowed(['wav', 'mp3'], 'Audio files only!')
    ])
    submit = SubmitField('Save Voice Model')

class AudioClipForm(FlaskForm):
    name = StringField('Clip Name', validators=[DataRequired(), Length(min=2, max=64)])
    text_content = TextAreaField('Text Content', validators=[DataRequired(), Length(max=1000)])
    flow_step = StringField('Flow Step', validators=[Optional(), Length(max=64)])
    sentiment = SelectField('Sentiment', choices=[
        ('', 'Select Sentiment'),
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative')
    ], validators=[Optional()])
    voice_model_id = SelectField('Voice Model', coerce=int, validators=[DataRequired()])
    language_id = SelectField('Language', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Generate Audio Clip')
    
    def __init__(self, *args, **kwargs):
        super(AudioClipForm, self).__init__(*args, **kwargs)
        self.language_id.choices = [(l.id, l.name) for l in Language.query.filter_by(is_active=True).all()]
