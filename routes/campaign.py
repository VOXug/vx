from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from datetime import datetime
from models import db, Campaign, ConversationFlow, VoterList, CallLog
from forms.campaign import CampaignForm
from utils.twilio_client import make_call

campaign_bp = Blueprint('campaign', __name__, url_prefix='/campaign')

@campaign_bp.route('/')
@login_required
def index():
    campaigns = Campaign.query.all()
    return render_template('campaign/index.html', title='Campaigns', campaigns=campaigns)

@campaign_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_campaign():
    form = CampaignForm()
    
    # Populate select fields
    form.conversation_flow_id.choices = [(f.id, f.name) for f in ConversationFlow.query.filter_by(is_active=True).all()]
    form.voter_list_id.choices = [(l.id, l.name) for l in VoterList.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        campaign = Campaign(
            name=form.name.data,
            description=form.description.data,
            status='draft',
            max_calls_per_day=form.max_calls_per_day.data,
            max_calls_per_hour=form.max_calls_per_hour.data,
            retry_attempts=form.retry_attempts.data,
            retry_delay_minutes=form.retry_delay_minutes.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            conversation_flow_id=form.conversation_flow_id.data,
            voter_list_id=form.voter_list_id.data
        )
        db.session.add(campaign)
        db.session.commit()
        
        flash(f'Campaign "{form.name.data}" created successfully.', 'success')
        return redirect(url_for('campaign.index'))
    
    return render_template('campaign/form.html', title='Create Campaign', form=form)

@campaign_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    form = CampaignForm(obj=campaign)
    
    # Populate select fields
    form.conversation_flow_id.choices = [(f.id, f.name) for f in ConversationFlow.query.filter_by(is_active=True).all()]
    form.voter_list_id.choices = [(l.id, l.name) for l in VoterList.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        campaign.name = form.name.data
        campaign.description = form.description.data
        campaign.max_calls_per_day = form.max_calls_per_day.data
        campaign.max_calls_per_hour = form.max_calls_per_hour.data
        campaign.retry_attempts = form.retry_attempts.data
        campaign.retry_delay_minutes = form.retry_delay_minutes.data
        campaign.start_date = form.start_date.data
        campaign.end_date = form.end_date.data
        campaign.conversation_flow_id = form.conversation_flow_id.data
        campaign.voter_list_id = form.voter_list_id.data
        
        db.session.commit()
        flash(f'Campaign "{campaign.name}" updated successfully.', 'success')
        return redirect(url_for('campaign.index'))
    
    return render_template('campaign/form.html', title='Edit Campaign', form=form, campaign=campaign)

@campaign_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    
    # Check if the campaign has any call logs
    if campaign.call_logs:
        flash(f'Cannot delete campaign "{campaign.name}" as it has call logs. You can archive it instead.', 'danger')
        return redirect(url_for('campaign.index'))
    
    db.session.delete(campaign)
    db.session.commit()
    
    flash(f'Campaign "{campaign.name}" deleted successfully.', 'success')
    return redirect(url_for('campaign.index'))

@campaign_bp.route('/<int:id>/status/<status>', methods=['POST'])
@login_required
def update_status(id, status):
    campaign = Campaign.query.get_or_404(id)
    
    if status not in ['draft', 'active', 'paused', 'completed']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('campaign.index'))
    
    # If activating the campaign, check if it has a valid start date
    if status == 'active' and (not campaign.start_date or campaign.start_date > datetime.utcnow()):
        flash(f'Cannot activate campaign "{campaign.name}" as it has a future start date.', 'danger')
        return redirect(url_for('campaign.index'))
    
    # If activating the campaign, check if it has a valid end date
    if status == 'active' and (campaign.end_date and campaign.end_date < datetime.utcnow()):
        flash(f'Cannot activate campaign "{campaign.name}" as it has a past end date.', 'danger')
        return redirect(url_for('campaign.index'))
    
    campaign.status = status
    db.session.commit()
    
    flash(f'Campaign "{campaign.name}" status updated to {status}.', 'success')
    return redirect(url_for('campaign.index'))

@campaign_bp.route('/<int:id>/view')
@login_required
def view_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    
    # Get call logs for this campaign
    call_logs = CallLog.query.filter_by(campaign_id=campaign.id).order_by(CallLog.created_at.desc()).limit(100).all()
    
    # Get campaign statistics
    stats = {
        'total_calls': CallLog.query.filter_by(campaign_id=campaign.id).count(),
        'completed_calls': CallLog.query.filter_by(campaign_id=campaign.id, status='completed').count(),
        'failed_calls': CallLog.query.filter_by(campaign_id=campaign.id, status='failed').count(),
        'in_progress_calls': CallLog.query.filter_by(campaign_id=campaign.id, status='in-progress').count(),
        'positive_sentiment': CallLog.query.filter_by(campaign_id=campaign.id, sentiment='positive').count(),
        'neutral_sentiment': CallLog.query.filter_by(campaign_id=campaign.id, sentiment='neutral').count(),
        'negative_sentiment': CallLog.query.filter_by(campaign_id=campaign.id, sentiment='negative').count()
    }
    
    return render_template('campaign/view.html', title=f'View Campaign: {campaign.name}', campaign=campaign, call_logs=call_logs, stats=stats)

@campaign_bp.route('/<int:id>/test-call', methods=['POST'])
@login_required
def test_call(id):
    campaign = Campaign.query.get_or_404(id)
    phone_number = request.form.get('phone_number')
    
    if not phone_number:
        flash('Please provide a phone number for the test call.', 'danger')
        return redirect(url_for('campaign.view_campaign', id=campaign.id))
    
    # Make a test call
    try:
        call_sid = make_call(phone_number, campaign.id, test=True)
        flash(f'Test call initiated to {phone_number}. Call SID: {call_sid}', 'success')
    except Exception as e:
        flash(f'Error initiating test call: {str(e)}', 'danger')
    
    return redirect(url_for('campaign.view_campaign', id=campaign.id))
