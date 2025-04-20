from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required
import pandas as pd
import io
import os
from datetime import datetime, timedelta
from models import db, Campaign, CallLog, Language

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    # Get summary statistics for all campaigns
    stats = {
        'total_calls': CallLog.query.count(),
        'calls_today': CallLog.query.filter(
            CallLog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count(),
        'active_campaigns': Campaign.query.filter_by(status='active').count(),
        'success_rate': calculate_success_rate(),
        'language_distribution': get_language_distribution(),
        'sentiment_distribution': get_sentiment_distribution()
    }
    
    # Get recent call logs
    recent_calls = CallLog.query.order_by(CallLog.created_at.desc()).limit(10).all()
    
    return render_template('reports/index.html', title='Reports Dashboard', stats=stats, recent_calls=recent_calls)

@reports_bp.route('/calls')
@login_required
def call_logs():
    # Get filter parameters
    campaign_id = request.args.get('campaign_id', type=int)
    status = request.args.get('status')
    sentiment = request.args.get('sentiment')
    language = request.args.get('language')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build the query
    query = CallLog.query
    
    if campaign_id:
        query = query.filter_by(campaign_id=campaign_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if sentiment:
        query = query.filter_by(sentiment=sentiment)
    
    if language:
        query = query.filter_by(detected_language=language)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(CallLog.created_at >= start_date)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            # Add a day to include the end date
            end_date = end_date + timedelta(days=1)
            query = query.filter(CallLog.created_at < end_date)
        except ValueError:
            pass
    
    # Get all campaigns for the filter dropdown
    campaigns = Campaign.query.all()
    
    # Get all languages for the filter dropdown
    languages = Language.query.all()
    
    # Paginate the results
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    call_logs = query.order_by(CallLog.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template(
        'reports/call_logs.html',
        title='Call Logs',
        call_logs=call_logs,
        campaigns=campaigns,
        languages=languages,
        filters={
            'campaign_id': campaign_id,
            'status': status,
            'sentiment': sentiment,
            'language': language,
            'start_date': start_date,
            'end_date': end_date
        }
    )

@reports_bp.route('/export', methods=['GET'])
@login_required
def export_logs():
    # Get filter parameters
    campaign_id = request.args.get('campaign_id', type=int)
    status = request.args.get('status')
    sentiment = request.args.get('sentiment')
    language = request.args.get('language')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    format = request.args.get('format', 'csv')
    
    # Build the query
    query = CallLog.query
    
    if campaign_id:
        query = query.filter_by(campaign_id=campaign_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if sentiment:
        query = query.filter_by(sentiment=sentiment)
    
    if language:
        query = query.filter_by(detected_language=language)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(CallLog.created_at >= start_date)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            # Add a day to include the end date
            end_date = end_date + timedelta(days=1)
            query = query.filter(CallLog.created_at < end_date)
        except ValueError:
            pass
    
    # Get all call logs
    call_logs = query.order_by(CallLog.created_at.desc()).all()
    
    # Convert to DataFrame
    data = []
    for log in call_logs:
        campaign = Campaign.query.get(log.campaign_id)
        data.append({
            'ID': log.id,
            'Call SID': log.call_sid,
            'Phone Number': log.phone_number,
            'Campaign': campaign.name if campaign else 'Unknown',
            'Status': log.status,
            'Duration (seconds)': log.duration,
            'Language': log.detected_language,
            'Sentiment': log.sentiment,
            'Started At': log.started_at,
            'Ended At': log.ended_at,
            'Created At': log.created_at
        })
    
    df = pd.DataFrame(data)
    
    # Create a buffer to store the file
    buffer = io.BytesIO()
    
    # Export to the requested format
    if format == 'excel':
        df.to_excel(buffer, index=False)
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = f'call_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    else:  # Default to CSV
        df.to_csv(buffer, index=False)
        mimetype = 'text/csv'
        filename = f'call_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    # Reset buffer position
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )

@reports_bp.route('/analytics')
@login_required
def analytics():
    # Get date range parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Default to last 7 days if not specified
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    if not end_date:
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Parse dates
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        # Add a day to include the end date
        end_date_obj = end_date_obj + timedelta(days=1)
    except ValueError:
        # Default to last 7 days if parsing fails
        end_date_obj = datetime.utcnow()
        start_date_obj = end_date_obj - timedelta(days=7)
        start_date = start_date_obj.strftime('%Y-%m-%d')
        end_date = (end_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Get daily call totals
    daily_calls = get_daily_call_totals(start_date_obj, end_date_obj)
    
    # Get sentiment distribution
    sentiment_data = get_sentiment_distribution(start_date_obj, end_date_obj)
    
    # Get language distribution
    language_data = get_language_distribution(start_date_obj, end_date_obj)
    
    # Get regional distribution
    regional_data = get_regional_distribution(start_date_obj, end_date_obj)
    
    return render_template(
        'reports/analytics.html',
        title='Analytics',
        start_date=start_date,
        end_date=end_date,
        daily_calls=daily_calls,
        sentiment_data=sentiment_data,
        language_data=language_data,
        regional_data=regional_data
    )

def calculate_success_rate():
    """Calculate the overall success rate of calls"""
    total_calls = CallLog.query.count()
    if total_calls == 0:
        return 0
    
    completed_calls = CallLog.query.filter_by(status='completed').count()
    return round((completed_calls / total_calls) * 100, 2)

def get_language_distribution(start_date=None, end_date=None):
    """Get the distribution of calls by language"""
    query = db.session.query(
        CallLog.detected_language,
        db.func.count(CallLog.id)
    ).group_by(CallLog.detected_language)
    
    if start_date and end_date:
        query = query.filter(CallLog.created_at >= start_date, CallLog.created_at < end_date)
    
    results = query.all()
    
    # Convert to dictionary
    distribution = {}
    for language, count in results:
        if language:
            # Get the language name
            lang_obj = Language.query.filter_by(code=language).first()
            lang_name = lang_obj.name if lang_obj else language
            distribution[lang_name] = count
        else:
            distribution['Unknown'] = count
    
    return distribution

def get_sentiment_distribution(start_date=None, end_date=None):
    """Get the distribution of calls by sentiment"""
    query = db.session.query(
        CallLog.sentiment,
        db.func.count(CallLog.id)
    ).group_by(CallLog.sentiment)
    
    if start_date and end_date:
        query = query.filter(CallLog.created_at >= start_date, CallLog.created_at < end_date)
    
    results = query.all()
    
    # Convert to dictionary
    distribution = {
        'Positive': 0,
        'Neutral': 0,
        'Negative': 0,
        'Unknown': 0
    }
    
    for sentiment, count in results:
        if sentiment == 'positive':
            distribution['Positive'] = count
        elif sentiment == 'neutral':
            distribution['Neutral'] = count
        elif sentiment == 'negative':
            distribution['Negative'] = count
        else:
            distribution['Unknown'] = count
    
    return distribution

def get_regional_distribution(start_date=None, end_date=None):
    """Get the distribution of calls by region"""
    # This would require joining with the Voter table to get region information
    # For simplicity, we'll return a placeholder
    return {
        'Central': 25,
        'Eastern': 20,
        'Northern': 15,
        'Western': 30,
        'Unknown': 10
    }

def get_daily_call_totals(start_date, end_date):
    """Get the daily call totals within a date range"""
    # Calculate the number of days
    days = (end_date - start_date).days
    
    # Generate a list of dates
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Initialize the result dictionary
    result = {date.strftime('%Y-%m-%d'): 0 for date in dates}
    
    # Query the database for daily call counts
    query = db.session.query(
        db.func.date(CallLog.created_at),
        db.func.count(CallLog.id)
    ).filter(
        CallLog.created_at >= start_date,
        CallLog.created_at < end_date
    ).group_by(
        db.func.date(CallLog.created_at)
    )
    
    # Update the result dictionary with actual counts
    for date_str, count in query.all():
        if isinstance(date_str, str):
            result[date_str] = count
        else:
            result[date_str.strftime('%Y-%m-%d')] = count
    
    # Convert to list of dictionaries for easier use in templates
    return [{'date': date, 'count': count} for date, count in result.items()]
