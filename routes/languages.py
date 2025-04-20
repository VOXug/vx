from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Language

languages_bp = Blueprint('languages', __name__, url_prefix='/languages')

@languages_bp.route('/')
@login_required
def index():
    """Display all languages"""
    languages = Language.query.all()
    return render_template('languages/index.html', title='Languages', languages=languages)

@languages_bp.route('/add', methods=['POST'])
@login_required
def add():
    """Add a new language"""
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        region = request.form.get('region')
        is_active = True if request.form.get('is_active') else False
        
        if not name or not code:
            flash('Language name and code are required', 'danger')
            return redirect(url_for('languages.index'))
        
        language = Language(name=name, code=code, region=region, is_active=is_active)
        db.session.add(language)
        db.session.commit()
        
        flash('Language added successfully', 'success')
        return redirect(url_for('languages.index'))

@languages_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    """Edit a language"""
    language = Language.query.get_or_404(id)
    
    if request.method == 'POST':
        language.name = request.form.get('name', language.name)
        language.code = request.form.get('code', language.code)
        language.region = request.form.get('region', language.region)
        language.is_active = True if request.form.get('is_active') else False
        
        db.session.commit()
        flash('Language updated successfully', 'success')
    
    return redirect(url_for('languages.index'))

@languages_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a language"""
    language = Language.query.get_or_404(id)
    db.session.delete(language)
    db.session.commit()
    flash('Language deleted successfully', 'success')
    return redirect(url_for('languages.index'))
