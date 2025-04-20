from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, VoterList
import os
from werkzeug.utils import secure_filename
import csv
import pandas as pd

voters_bp = Blueprint('voters', __name__, url_prefix='/voters')

@voters_bp.route('/')
@login_required
def index():
    """Display all voter lists"""
    voter_lists = VoterList.query.all()
    return render_template('voters/index.html', title='Voter Lists', voter_lists=voter_lists)

@voters_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new voter list"""
    if request.method == 'POST':
        name = request.form.get('name')
        region = request.form.get('region')
        description = request.form.get('description')
        is_active = True if request.form.get('is_active') else False
        
        if not name:
            flash('List name is required', 'danger')
            return redirect(url_for('voters.index'))
        
        # Handle file upload
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('voters.index'))
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['VOTER_DATA_FOLDER'], filename)
        file.save(file_path)
        
        # Create voter list record
        voter_list = VoterList(
            name=name,
            region=region,
            description=description,
            file_path=file_path,
            is_active=is_active,
            created_by=current_user.id
        )
        
        # Process file to extract metadata
        try:
            if filename.endswith('.csv'):
                with open(file_path, 'r') as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    row_count = sum(1 for row in reader) + 1  # Include header
                    
                    voter_list.total_contacts = row_count - 1  # Exclude header
                    voter_list.metadata = {'columns': headers}
            
            elif filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
                voter_list.total_contacts = len(df)
                voter_list.metadata = {'columns': df.columns.tolist()}
            
            db.session.add(voter_list)
            db.session.commit()
            
            flash('Voter list uploaded successfully', 'success')
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
        
        return redirect(url_for('voters.index'))
    
    return render_template('voters/add.html', title='Add Voter List')

@voters_bp.route('/<int:id>')
@login_required
def view(id):
    """View a voter list"""
    voter_list = VoterList.query.get_or_404(id)
    
    # Get sample data
    sample_data = []
    try:
        if voter_list.file_path.endswith('.csv'):
            df = pd.read_csv(voter_list.file_path, nrows=5)
            sample_data = df.to_dict('records')
        elif voter_list.file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(voter_list.file_path, nrows=5)
            sample_data = df.to_dict('records')
    except Exception as e:
        flash(f'Error reading file: {str(e)}', 'danger')
    
    return render_template('voters/view.html', title=f'Voter List: {voter_list.name}', 
                          voter_list=voter_list, sample_data=sample_data)

@voters_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a voter list"""
    voter_list = VoterList.query.get_or_404(id)
    
    if request.method == 'POST':
        voter_list.name = request.form.get('name', voter_list.name)
        voter_list.region = request.form.get('region', voter_list.region)
        voter_list.description = request.form.get('description', voter_list.description)
        voter_list.is_active = True if request.form.get('is_active') else False
        
        db.session.commit()
        flash('Voter list updated successfully', 'success')
        return redirect(url_for('voters.view', id=id))
    
    return render_template('voters/edit.html', title=f'Edit Voter List: {voter_list.name}', 
                          voter_list=voter_list)

@voters_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a voter list"""
    voter_list = VoterList.query.get_or_404(id)
    
    # Delete the file if it exists
    if voter_list.file_path and os.path.exists(voter_list.file_path):
        os.remove(voter_list.file_path)
    
    db.session.delete(voter_list)
    db.session.commit()
    flash('Voter list deleted successfully', 'success')
    return redirect(url_for('voters.index'))
