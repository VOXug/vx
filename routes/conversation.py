from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
import json
from models import db, ConversationFlow, Language
from forms.conversation import ConversationFlowForm

conversation_bp = Blueprint('conversation', __name__, url_prefix='/conversation')

@conversation_bp.route('/')
@login_required
def index():
    flows = ConversationFlow.query.all()
    return render_template('conversation/index.html', title='Conversation Flows', flows=flows)

@conversation_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_flow():
    form = ConversationFlowForm()
    languages = Language.query.filter_by(is_active=True).all()
    
    if form.validate_on_submit():
        # Create a basic flow structure
        flow_data = {
            'steps': [
                {
                    'id': 'intro',
                    'type': 'message',
                    'name': 'Introduction',
                    'text': form.intro_text.data,
                    'next': 'talking_point_1'
                },
                {
                    'id': 'talking_point_1',
                    'type': 'message',
                    'name': 'Talking Point 1',
                    'text': form.talking_point_1.data,
                    'next': 'response_1'
                },
                {
                    'id': 'response_1',
                    'type': 'response',
                    'name': 'Voter Response 1',
                    'branches': {
                        'positive': 'positive_reply_1',
                        'neutral': 'neutral_reply_1',
                        'negative': 'negative_reply_1'
                    }
                },
                {
                    'id': 'positive_reply_1',
                    'type': 'message',
                    'name': 'Positive Reply 1',
                    'text': form.positive_reply_1.data,
                    'next': 'outro'
                },
                {
                    'id': 'neutral_reply_1',
                    'type': 'message',
                    'name': 'Neutral Reply 1',
                    'text': form.neutral_reply_1.data,
                    'next': 'outro'
                },
                {
                    'id': 'negative_reply_1',
                    'type': 'message',
                    'name': 'Negative Reply 1',
                    'text': form.negative_reply_1.data,
                    'next': 'outro'
                },
                {
                    'id': 'outro',
                    'type': 'message',
                    'name': 'Outro',
                    'text': form.outro_text.data,
                    'next': 'end'
                },
                {
                    'id': 'end',
                    'type': 'end',
                    'name': 'End of Conversation'
                }
            ]
        }
        
        flow = ConversationFlow(
            name=form.name.data,
            description=form.description.data,
            flow_data=json.dumps(flow_data),
            is_active=form.is_active.data
        )
        db.session.add(flow)
        db.session.commit()
        
        flash(f'Conversation flow "{form.name.data}" created successfully.', 'success')
        return redirect(url_for('conversation.edit_flow', id=flow.id))
    
    return render_template('conversation/form.html', title='Create Conversation Flow', form=form, languages=languages)

@conversation_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_flow(id):
    flow = ConversationFlow.query.get_or_404(id)
    languages = Language.query.filter_by(is_active=True).all()
    
    if request.method == 'GET':
        form = ConversationFlowForm(obj=flow)
        
        # Populate form fields from flow_data
        flow_data = flow.get_flow_data()
        for step in flow_data.get('steps', []):
            if step['id'] == 'intro':
                form.intro_text.data = step.get('text', '')
            elif step['id'] == 'talking_point_1':
                form.talking_point_1.data = step.get('text', '')
            elif step['id'] == 'positive_reply_1':
                form.positive_reply_1.data = step.get('text', '')
            elif step['id'] == 'neutral_reply_1':
                form.neutral_reply_1.data = step.get('text', '')
            elif step['id'] == 'negative_reply_1':
                form.negative_reply_1.data = step.get('text', '')
            elif step['id'] == 'outro':
                form.outro_text.data = step.get('text', '')
    else:
        form = ConversationFlowForm(request.form)
        
        if form.validate_on_submit():
            # Update basic flow information
            flow.name = form.name.data
            flow.description = form.description.data
            flow.is_active = form.is_active.data
            
            # Update flow_data with form values
            flow_data = flow.get_flow_data()
            for step in flow_data.get('steps', []):
                if step['id'] == 'intro':
                    step['text'] = form.intro_text.data
                elif step['id'] == 'talking_point_1':
                    step['text'] = form.talking_point_1.data
                elif step['id'] == 'positive_reply_1':
                    step['text'] = form.positive_reply_1.data
                elif step['id'] == 'neutral_reply_1':
                    step['text'] = form.neutral_reply_1.data
                elif step['id'] == 'negative_reply_1':
                    step['text'] = form.negative_reply_1.data
                elif step['id'] == 'outro':
                    step['text'] = form.outro_text.data
            
            flow.set_flow_data(flow_data)
            db.session.commit()
            
            flash(f'Conversation flow "{flow.name}" updated successfully.', 'success')
            return redirect(url_for('conversation.index'))
    
    return render_template('conversation/form.html', title='Edit Conversation Flow', form=form, flow=flow, languages=languages)

@conversation_bp.route('/<int:id>/builder', methods=['GET'])
@login_required
def flow_builder(id):
    flow = ConversationFlow.query.get_or_404(id)
    languages = Language.query.filter_by(is_active=True).all()
    
    return render_template('conversation/builder.html', title='Flow Builder', flow=flow, languages=languages)

@conversation_bp.route('/<int:id>/data', methods=['GET'])
@login_required
def get_flow_data(id):
    flow = ConversationFlow.query.get_or_404(id)
    return jsonify(flow.get_flow_data())

@conversation_bp.route('/<int:id>/data', methods=['POST'])
@login_required
def update_flow_data(id):
    flow = ConversationFlow.query.get_or_404(id)
    
    try:
        flow_data = request.json
        flow.set_flow_data(flow_data)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Flow updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@conversation_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_flow(id):
    flow = ConversationFlow.query.get_or_404(id)
    
    # Check if the flow is being used by any campaigns
    if flow.campaigns:
        flash(f'Cannot delete flow "{flow.name}" as it is being used by campaigns.', 'danger')
        return redirect(url_for('conversation.index'))
    
    db.session.delete(flow)
    db.session.commit()
    
    flash(f'Conversation flow "{flow.name}" deleted successfully.', 'success')
    return redirect(url_for('conversation.index'))
