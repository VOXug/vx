from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Campaign, CallLog, VoterList
from datetime import datetime

callcenter_bp = Blueprint('callcenter', __name__, url_prefix='/callcenter')

@callcenter_bp.route('/')
@login_required
def index():
    """Display call center dashboard"""
    # Get active campaigns
    try:
        active_campaigns = Campaign.query.filter_by(is_active=True).all()
    except Exception as e:
        active_campaigns = []
        print(f"Error fetching campaigns: {str(e)}")
    
    # Get recent calls
    try:
        recent_calls = CallLog.query.order_by(CallLog.created_at.desc()).limit(10).all()
    except Exception as e:
        recent_calls = []
        print(f"Error fetching recent calls: {str(e)}")
    
    # Get call statistics
    try:
        total_calls = CallLog.query.count()
        completed_calls = CallLog.query.filter_by(status='completed').count()
        in_progress_calls = CallLog.query.filter_by(status='in-progress').count()
        failed_calls = CallLog.query.filter_by(status='failed').count()
    except Exception as e:
        total_calls = 0
        completed_calls = 0
        in_progress_calls = 0
        failed_calls = 0
        print(f"Error fetching call statistics: {str(e)}")
    
    # Calculate success rate
    success_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0
    
    return render_template('callcenter/index.html', 
                          title='Call Center',
                          active_campaigns=active_campaigns,
                          recent_calls=recent_calls,
                          total_calls=total_calls,
                          completed_calls=completed_calls,
                          in_progress_calls=in_progress_calls,
                          failed_calls=failed_calls,
                          success_rate=success_rate)

@callcenter_bp.route('/calls')
@login_required
def calls():
    """Display all calls with filtering options"""
    # Get filter parameters
    campaign_id = request.args.get('campaign_id', type=int)
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    try:
        # Base query
        query = CallLog.query
        
        # Apply filters
        if campaign_id:
            query = query.filter_by(campaign_id=campaign_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(CallLog.created_at >= date_from)
        
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(CallLog.created_at <= date_to)
        
        # Get results with pagination
        page = request.args.get('page', 1, type=int)
        calls = query.order_by(CallLog.created_at.desc()).paginate(page=page, per_page=20)
    except Exception as e:
        print(f"Error fetching call logs: {str(e)}")
        calls = None
    
    # Get campaigns for filter dropdown
    try:
        campaigns = Campaign.query.all()
    except Exception as e:
        print(f"Error fetching campaigns: {str(e)}")
        campaigns = []
    
    return render_template('callcenter/calls.html', 
                          title='Call Logs',
                          calls=calls,
                          campaigns=campaigns)

@callcenter_bp.route('/call/<int:id>')
@login_required
def call_detail(id):
    """View details of a specific call"""
    try:
        call = CallLog.query.get_or_404(id)
    except Exception as e:
        print(f"Error fetching call details: {str(e)}")
        call = None
    return render_template('callcenter/call_detail.html', 
                          title='Call Details',
                          call=call)

@callcenter_bp.route('/live')
@login_required
def live_dashboard():
    """Display live call center dashboard with real-time updates"""
    # Get active campaigns
    try:
        active_campaigns = Campaign.query.filter_by(is_active=True).all()
    except Exception as e:
        active_campaigns = []
        print(f"Error fetching campaigns: {str(e)}")
    
    return render_template('callcenter/live.html', 
                          title='Live Call Center',
                          active_campaigns=active_campaigns)

@callcenter_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for getting current call statistics"""
    try:
        # Get call statistics
        total_calls = CallLog.query.count()
        completed_calls = CallLog.query.filter_by(status='completed').count()
        in_progress_calls = CallLog.query.filter_by(status='in-progress').count()
        failed_calls = CallLog.query.filter_by(status='failed').count()
        
        # Calculate success rate
        success_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0
    except Exception as e:
        print(f"Error fetching call statistics: {str(e)}")
        total_calls = 0
        completed_calls = 0
        in_progress_calls = 0
        failed_calls = 0
        success_rate = 0
    
    # Get campaign-specific stats
    campaign_stats = []
    try:
        campaigns = Campaign.query.filter_by(is_active=True).all()
        
        for campaign in campaigns:
            try:
                campaign_total = CallLog.query.filter_by(campaign_id=campaign.id).count()
                campaign_completed = CallLog.query.filter_by(campaign_id=campaign.id, status='completed').count()
                campaign_stats.append({
                    'id': campaign.id,
                    'name': campaign.name,
                    'total_calls': campaign_total,
                    'completed_calls': campaign_completed,
                    'completion_rate': (campaign_completed / campaign_total * 100) if campaign_total > 0 else 0
                })
            except Exception as e:
                print(f"Error processing campaign {campaign.id}: {str(e)}")
    except Exception as e:
        print(f"Error fetching campaigns: {str(e)}")
    
    return jsonify({
        'total_calls': total_calls,
        'completed_calls': completed_calls,
        'in_progress_calls': in_progress_calls,
        'failed_calls': failed_calls,
        'success_rate': success_rate,
        'campaign_stats': campaign_stats
    })

@callcenter_bp.route('/api/recent-calls')
@login_required
def api_recent_calls():
    """API endpoint for getting recent calls"""
    calls_data = []
    try:
        recent_calls = CallLog.query.order_by(CallLog.created_at.desc()).limit(10).all()
        
        for call in recent_calls:
            try:
                calls_data.append({
                    'id': call.id,
                    'phone_number': call.phone_number,
                    'duration': call.duration,
                    'status': call.status,
                    'created_at': call.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'campaign_id': call.campaign_id,
                    'campaign_name': call.campaign.name if call.campaign else 'Unknown'
                })
            except Exception as e:
                print(f"Error processing call {call.id}: {str(e)}")
    except Exception as e:
        print(f"Error fetching recent calls: {str(e)}")
    
    return jsonify(calls_data)
