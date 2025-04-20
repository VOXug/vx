from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from models import Language

class LanguageForm(FlaskForm):
    name = StringField('Language Name', validators=[DataRequired(), Length(min=2, max=64)])
    code = StringField('Language Code', validators=[DataRequired(), Length(min=2, max=10)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Language')
    
    def __init__(self, *args, **kwargs):
        super(LanguageForm, self).__init__(*args, **kwargs)
        self.original_code = kwargs.get('obj', None).code if kwargs.get('obj', None) else None
    
    def validate_code(self, code):
        if self.original_code and self.original_code == code.data:
            return
        language = Language.query.filter_by(code=code.data).first()
        if language is not None:
            raise ValidationError('Language code already exists. Please use a different code.')
