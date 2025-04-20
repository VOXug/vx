from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Language
from forms.language import LanguageForm

language_bp = Blueprint('language', __name__, url_prefix='/language')

@language_bp.route('/')
@login_required
def index():
    languages = Language.query.all()
    return render_template('language/index.html', title='Languages', languages=languages)

@language_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_language():
    form = LanguageForm()
    
    if form.validate_on_submit():
        language = Language(
            name=form.name.data,
            code=form.code.data,
            is_active=form.is_active.data
        )
        db.session.add(language)
        db.session.commit()
        
        flash(f'Language "{form.name.data}" added successfully.', 'success')
        return redirect(url_for('language.index'))
    
    return render_template('language/form.html', title='Add Language', form=form)

@language_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_language(id):
    language = Language.query.get_or_404(id)
    form = LanguageForm(obj=language)
    
    if form.validate_on_submit():
        language.name = form.name.data
        language.code = form.code.data
        language.is_active = form.is_active.data
        
        db.session.commit()
        flash(f'Language "{language.name}" updated successfully.', 'success')
        return redirect(url_for('language.index'))
    
    return render_template('language/form.html', title='Edit Language', form=form, language=language)

@language_bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_language(id):
    language = Language.query.get_or_404(id)
    language.is_active = not language.is_active
    db.session.commit()
    
    status = 'activated' if language.is_active else 'deactivated'
    flash(f'Language "{language.name}" {status} successfully.', 'success')
    return redirect(url_for('language.index'))

@language_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_language(id):
    language = Language.query.get_or_404(id)
    
    # Check if the language is being used by any audio clips
    if language.audio_clips:
        flash(f'Cannot delete language "{language.name}" as it is being used by audio clips.', 'danger')
        return redirect(url_for('language.index'))
    
    db.session.delete(language)
    db.session.commit()
    
    flash(f'Language "{language.name}" deleted successfully.', 'success')
    return redirect(url_for('language.index'))
