from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, ConversationFlow, Language

flows_bp = Blueprint('flows', __name__, url_prefix='/flows')

@flows_bp.route('/')
@login_required
def index():
    """Display all conversation flows"""
    flows = ConversationFlow.query.all()
    languages = Language.query.all()
    return render_template('flows/index.html', title='Conversation Flows', flows=flows, languages=languages)

@flows_bp.route('/add', methods=['POST'])
@login_required
def add():
    """Add a new conversation flow"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        flow_type = request.form.get('flow_type')
        is_active = True if request.form.get('is_active') else False
        
        if not name:
            flash('Flow name is required', 'danger')
            return redirect(url_for('flows.index'))
        
        flow = ConversationFlow(
            name=name,
            description=description,
            flow_type=flow_type,
            is_active=is_active,
            created_by=current_user.id
        )
        
        db.session.add(flow)
        db.session.commit()
        
        # Handle language associations if needed
        language_ids = request.form.getlist('languages')
        if language_ids:
            languages = Language.query.filter(Language.id.in_(language_ids)).all()
            flow.languages = languages
            db.session.commit()
        
        flash('Conversation flow created successfully', 'success')
        return redirect(url_for('flows.index'))

@flows_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    """Edit a conversation flow"""
    flow = ConversationFlow.query.get_or_404(id)
    
    if request.method == 'POST':
        flow.name = request.form.get('name', flow.name)
        flow.description = request.form.get('description', flow.description)
        flow.flow_type = request.form.get('flow_type', flow.flow_type)
        flow.is_active = True if request.form.get('is_active') else False
        
        # Handle language associations if needed
        language_ids = request.form.getlist('languages')
        if language_ids:
            languages = Language.query.filter(Language.id.in_(language_ids)).all()
            flow.languages = languages
        
        db.session.commit()
        flash('Conversation flow updated successfully', 'success')
    
    return redirect(url_for('flows.index'))

@flows_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a conversation flow"""
    flow = ConversationFlow.query.get_or_404(id)
    db.session.delete(flow)
    db.session.commit()
    flash('Conversation flow deleted successfully', 'success')
    return redirect(url_for('flows.index'))

@flows_bp.route('/<int:id>/steps', methods=['GET', 'POST'])
@login_required
def steps(id):
    """Manage steps for a conversation flow"""
    flow = ConversationFlow.query.get_or_404(id)
    
    if request.method == 'POST':
        # Handle step updates
        steps_data = request.json.get('steps', [])
        
        # Clear existing steps and add new ones
        flow.steps = []
        for i, step_data in enumerate(steps_data):
            step = {
                'order': i,
                'content': step_data.get('content', ''),
                'type': step_data.get('type', 'message')
            }
            flow.steps.append(step)
        
        db.session.commit()
        return jsonify({'success': True})
    
    return render_template('flows/steps.html', title=f'Edit Flow: {flow.name}', flow=flow)
