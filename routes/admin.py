from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, APIConfig, Language
from datetime import datetime

# Temporary form class for API Config until we implement the proper forms
class APIConfigForm:
    def __init__(self):
        self.name = None
        self.key = None
        self.value = None
        self.is_active = None
    
    def validate_on_submit(self):
        return False

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Get summary statistics for the dashboard
    stats = {
        'total_campaigns': 0,
        'active_campaigns': 0,
        'total_calls': 0,
        'calls_today': 0,
        'success_rate': 0,
        'languages': [lang.name for lang in Language.query.all()]
    }
    
    # Get recent call logs for the dashboard
    recent_calls = []  # Empty for demo
    
    return render_template('admin/dashboard.html', title='Dashboard', stats=stats, recent_calls=recent_calls)

@admin_bp.route('/api-config', methods=['GET', 'POST'])
@login_required
def api_config():
    form = APIConfigForm()
    
    if form.validate_on_submit():
        # Check if config already exists
        config = APIConfig.query.filter_by(name=form.name.data).first()
        
        if config:
            # Update existing config
            config.key = form.key.data
            config.value = form.value.data
            config.is_active = form.is_active.data
            flash(f'API configuration "{form.name.data}" updated successfully.', 'success')
        else:
            # Create new config
            config = APIConfig(
                name=form.name.data,
                key=form.key.data,
                value=form.value.data,
                is_active=form.is_active.data
            )
            db.session.add(config)
            flash(f'API configuration "{form.name.data}" added successfully.', 'success')
        
        db.session.commit()
        return redirect(url_for('admin.api_config'))
    
    # Get all API configs
    configs = APIConfig.query.all()
    
    return render_template('admin/api_config.html', title='API Configuration', form=form, configs=configs)

@admin_bp.route('/api-config/<int:id>/delete', methods=['POST'])
@login_required
def delete_api_config(id):
    config = APIConfig.query.get_or_404(id)
    db.session.delete(config)
    db.session.commit()
    flash(f'API configuration "{config.name}" deleted successfully.', 'success')
    return redirect(url_for('admin.api_config'))

@admin_bp.route('/users')
@login_required
def users():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    users = User.query.all()
    return render_template('admin/users.html', title='User Management', users=users)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    form = UserForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=form.is_admin.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash(f'User "{form.username.data}" created successfully.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', title='Add User', form=form)

@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        flash(f'User "{user.username}" updated successfully.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', title='Edit User', form=form, user=user)

@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    if id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted successfully.', 'success')
    return redirect(url_for('admin.users'))
