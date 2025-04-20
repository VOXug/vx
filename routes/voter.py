from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
import uuid
import pandas as pd
import csv
from models import db, VoterList, Voter, DoNotCallList
from forms.voter import VoterListForm, DoNotCallForm

voter_bp = Blueprint('voter', __name__, url_prefix='/voter')

@voter_bp.route('/')
@login_required
def index():
    voter_lists = VoterList.query.all()
    return render_template('voter/index.html', title='Voter Lists', voter_lists=voter_lists)

@voter_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_voter_list():
    form = VoterListForm()
    
    if form.validate_on_submit():
        # Save the uploaded voter list file
        voter_file = form.voter_file.data
        filename = secure_filename(f"{uuid.uuid4()}_{voter_file.filename}")
        file_path = os.path.join(current_app.config['VOTER_DATA_FOLDER'], filename)
        voter_file.save(file_path)
        
        # Create a new voter list record
        voter_list = VoterList(
            name=form.name.data,
            description=form.description.data,
            file_path=file_path,
            is_active=True
        )
        db.session.add(voter_list)
        db.session.commit()
        
        # Process the voter list file
        process_voter_list(voter_list.id)
        
        flash(f'Voter list "{form.name.data}" uploaded and processed successfully.', 'success')
        return redirect(url_for('voter.index'))
    
    return render_template('voter/form.html', title='Add Voter List', form=form)

@voter_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_voter_list(id):
    voter_list = VoterList.query.get_or_404(id)
    form = VoterListForm(obj=voter_list)
    
    if form.validate_on_submit():
        voter_list.name = form.name.data
        voter_list.description = form.description.data
        
        if form.voter_file.data:
            # Save the new uploaded voter list file
            voter_file = form.voter_file.data
            filename = secure_filename(f"{uuid.uuid4()}_{voter_file.filename}")
            file_path = os.path.join(current_app.config['VOTER_DATA_FOLDER'], filename)
            voter_file.save(file_path)
            
            # Update the file path
            voter_list.file_path = file_path
            
            # Process the new voter list file
            process_voter_list(voter_list.id)
            
            flash(f'Voter list "{voter_list.name}" updated and processed successfully.', 'success')
        else:
            flash(f'Voter list "{voter_list.name}" updated successfully.', 'success')
        
        db.session.commit()
        return redirect(url_for('voter.index'))
    
    return render_template('voter/form.html', title='Edit Voter List', form=form, voter_list=voter_list)

@voter_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_voter_list(id):
    voter_list = VoterList.query.get_or_404(id)
    
    # Check if the voter list is being used by any campaigns
    if voter_list.campaigns:
        flash(f'Cannot delete voter list "{voter_list.name}" as it is being used by campaigns.', 'danger')
        return redirect(url_for('voter.index'))
    
    # Delete the voter list file
    if os.path.exists(voter_list.file_path):
        os.remove(voter_list.file_path)
    
    db.session.delete(voter_list)
    db.session.commit()
    
    flash(f'Voter list "{voter_list.name}" deleted successfully.', 'success')
    return redirect(url_for('voter.index'))

@voter_bp.route('/<int:id>/view')
@login_required
def view_voter_list(id):
    voter_list = VoterList.query.get_or_404(id)
    
    # Get all voters from this list
    # In a real implementation, you would query the database
    # For now, we'll just read the file
    voters = []
    try:
        extension = os.path.splitext(voter_list.file_path)[1].lower()
        
        if extension == '.csv':
            with open(voter_list.file_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Skip header row
                for row in reader:
                    if len(row) > 0:
                        voters.append({
                            'phone_number': row[0],
                            'region': row[1] if len(row) > 1 else None
                        })
        elif extension in ['.xls', '.xlsx']:
            df = pd.read_excel(voter_list.file_path)
            for _, row in df.iterrows():
                voters.append({
                    'phone_number': row[0],
                    'region': row[1] if len(row) > 1 else None
                })
        else:
            with open(voter_list.file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        voters.append({
                            'phone_number': line,
                            'region': None
                        })
    except Exception as e:
        flash(f'Error reading voter list file: {str(e)}', 'danger')
    
    return render_template('voter/view.html', title=f'View Voter List: {voter_list.name}', voter_list=voter_list, voters=voters)

@voter_bp.route('/do-not-call')
@login_required
def do_not_call():
    do_not_call_list = DoNotCallList.query.all()
    return render_template('voter/do_not_call.html', title='Do Not Call List', do_not_call_list=do_not_call_list)

@voter_bp.route('/do-not-call/add', methods=['GET', 'POST'])
@login_required
def add_do_not_call():
    form = DoNotCallForm()
    
    if form.validate_on_submit():
        # Format the phone number
        phone_number = format_phone_number(form.phone_number.data)
        
        # Check if the phone number is already in the do not call list
        existing = DoNotCallList.query.filter_by(phone_number=phone_number).first()
        if existing:
            flash(f'Phone number {phone_number} is already in the Do Not Call list.', 'warning')
            return redirect(url_for('voter.do_not_call'))
        
        # Add the phone number to the do not call list
        do_not_call = DoNotCallList(
            phone_number=phone_number,
            reason=form.reason.data
        )
        db.session.add(do_not_call)
        
        # Update any existing voter records
        voter = Voter.query.filter_by(phone_number=phone_number).first()
        if voter:
            voter.do_not_call = True
        
        db.session.commit()
        flash(f'Phone number {phone_number} added to the Do Not Call list.', 'success')
        return redirect(url_for('voter.do_not_call'))
    
    return render_template('voter/do_not_call_form.html', title='Add to Do Not Call List', form=form)

@voter_bp.route('/do-not-call/<int:id>/delete', methods=['POST'])
@login_required
def delete_do_not_call(id):
    do_not_call = DoNotCallList.query.get_or_404(id)
    
    # Update any existing voter records
    voter = Voter.query.filter_by(phone_number=do_not_call.phone_number).first()
    if voter:
        voter.do_not_call = False
    
    db.session.delete(do_not_call)
    db.session.commit()
    
    flash(f'Phone number {do_not_call.phone_number} removed from the Do Not Call list.', 'success')
    return redirect(url_for('voter.do_not_call'))

def process_voter_list(voter_list_id):
    """
    Process a voter list file and add the voters to the database.
    
    Args:
        voter_list_id (int): The ID of the voter list to process
    """
    voter_list = VoterList.query.get(voter_list_id)
    if not voter_list:
        return
    
    try:
        # Get the do not call list
        do_not_call_numbers = set(dnc.phone_number for dnc in DoNotCallList.query.all())
        
        # Process the file based on its extension
        extension = os.path.splitext(voter_list.file_path)[1].lower()
        
        total_numbers = 0
        valid_numbers = 0
        
        if extension == '.csv':
            with open(voter_list.file_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader, None)  # Skip header row if it exists
                
                for row in reader:
                    if len(row) > 0:
                        total_numbers += 1
                        phone_number = format_phone_number(row[0])
                        
                        if phone_number:
                            valid_numbers += 1
                            region = row[1] if len(row) > 1 else None
                            add_voter(phone_number, region, do_not_call_numbers)
        
        elif extension in ['.xls', '.xlsx']:
            df = pd.read_excel(voter_list.file_path)
            
            for _, row in df.iterrows():
                total_numbers += 1
                phone_number = format_phone_number(str(row[0]))
                
                if phone_number:
                    valid_numbers += 1
                    region = row[1] if len(row) > 1 else None
                    add_voter(phone_number, region, do_not_call_numbers)
        
        else:  # Assume it's a text file with one number per line
            with open(voter_list.file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        total_numbers += 1
                        phone_number = format_phone_number(line)
                        
                        if phone_number:
                            valid_numbers += 1
                            add_voter(phone_number, None, do_not_call_numbers)
        
        # Update the voter list with the counts
        voter_list.total_numbers = total_numbers
        voter_list.valid_numbers = valid_numbers
        db.session.commit()
        
    except Exception as e:
        # Log the error
        print(f"Error processing voter list {voter_list_id}: {str(e)}")

def format_phone_number(phone_number):
    """
    Format a phone number to the standard format (+256xxxxxxxxx).
    
    Args:
        phone_number (str): The phone number to format
        
    Returns:
        str: The formatted phone number, or None if invalid
    """
    # Remove any non-digit characters
    digits = ''.join(c for c in phone_number if c.isdigit())
    
    # Check if we have enough digits
    if len(digits) < 9:
        return None
    
    # If it starts with 0, remove the 0 and add +256
    if digits.startswith('0'):
        digits = digits[1:]
        return f"+256{digits}"
    
    # If it starts with 256, add +
    elif digits.startswith('256'):
        return f"+{digits}"
    
    # If it's just 9 digits, assume it's a Uganda number without the country code
    elif len(digits) == 9:
        return f"+256{digits}"
    
    # Otherwise, return as is with + prefix
    else:
        return f"+{digits}"

def add_voter(phone_number, region, do_not_call_numbers):
    """
    Add a voter to the database if they don't already exist.
    
    Args:
        phone_number (str): The formatted phone number
        region (str): The region of the voter
        do_not_call_numbers (set): Set of phone numbers in the do not call list
    """
    # Check if the voter already exists
    voter = Voter.query.filter_by(phone_number=phone_number).first()
    
    if voter:
        # Update the region if provided
        if region:
            voter.region = region
    else:
        # Create a new voter
        voter = Voter(
            phone_number=phone_number,
            region=region,
            do_not_call=phone_number in do_not_call_numbers
        )
        db.session.add(voter)
    
    db.session.commit()
