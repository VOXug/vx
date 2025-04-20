from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class VoterListForm(FlaskForm):
    name = StringField('List Name', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    voter_file = FileField('Voter List File', validators=[
        FileRequired(),
        FileAllowed(['csv', 'txt', 'xls', 'xlsx'], 'CSV, TXT, or Excel files only!')
    ])
    submit = SubmitField('Save Voter List')

class DoNotCallForm(FlaskForm):
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=256)])
    submit = SubmitField('Add to Do Not Call List')
