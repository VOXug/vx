from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from twilio.twiml.voice_response import VoiceResponse
import logging
from models import db, CallLog, CallStep
from utils.twilio_client import generate_twiml_for_step, process_voter_response
from utils.openai_client import transcribe_audio, analyze_response

# Set up logging
logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/webhook', methods=['POST'])
def call_webhook():
    """
    Webhook for incoming Twilio calls.
    This is the entry point for all calls.
    """
    try:
        # Get the call SID from the request
        call_sid = request.values.get('CallSid')
        
        # Log the incoming call
        logger.info(f"Incoming call webhook, Call SID: {call_sid}")
        
        # Find the call log for this call
        call_log = CallLog.query.filter_by(call_sid=call_sid).first()
        
        if not call_log:
            # If no call log is found, this is an unexpected call
            logger.warning(f"No call log found for Call SID: {call_sid}")
            return error_response()
        
        # Update the call status
        call_log.status = 'in-progress'
        db.session.commit()
        
        # Generate TwiML for the first step of the conversation
        return generate_twiml_for_step(call_log.id)
        
    except Exception as e:
        logger.error(f"Error in call webhook: {str(e)}")
        return error_response()

@api_bp.route('/call-status', methods=['POST'])
def call_status_callback():
    """
    Callback for Twilio call status updates.
    """
    try:
        # Get the call log ID from the request
        call_log_id = request.args.get('call_log_id')
        
        # Get the call status from the request
        call_status = request.values.get('CallStatus')
        call_sid = request.values.get('CallSid')
        call_duration = request.values.get('CallDuration')
        
        logger.info(f"Call status callback: {call_status}, Call SID: {call_sid}, Call Log ID: {call_log_id}")
        
        # Find the call log
        call_log = CallLog.query.get(call_log_id)
        
        if call_log:
            # Update the call log
            call_log.status = call_status
            
            if call_status == 'completed':
                call_log.ended_at = db.func.now()
                if call_duration:
                    call_log.duration = int(call_duration)
            
            db.session.commit()
        
        return '', 204
        
    except Exception as e:
        logger.error(f"Error in call status callback: {str(e)}")
        return '', 500

@api_bp.route('/call-step/<int:call_log_id>/<step_id>', methods=['POST'])
def call_step(call_log_id, step_id):
    """
    Endpoint for handling a specific step in the conversation.
    """
    try:
        logger.info(f"Call step: {step_id}, Call Log ID: {call_log_id}")
        
        # Generate TwiML for this step
        return generate_twiml_for_step(call_log_id, step_id)
        
    except Exception as e:
        logger.error(f"Error in call step: {str(e)}")
        return error_response()

@api_bp.route('/process-response/<int:call_log_id>/<step_id>', methods=['POST'])
def process_response(call_log_id, step_id):
    """
    Process a voter's response.
    """
    try:
        # Get the speech result from Twilio
        speech_result = request.values.get('SpeechResult')
        
        logger.info(f"Processing response for step {step_id}, Call Log ID: {call_log_id}")
        logger.info(f"Speech result: {speech_result}")
        
        if not speech_result:
            # If no speech was detected, try again
            return generate_twiml_for_step(call_log_id, step_id)
        
        # Process the response using GPT-4
        next_step_id, sentiment, language = process_voter_response(call_log_id, step_id, speech_result)
        
        if next_step_id:
            # Generate TwiML for the next step
            return generate_twiml_for_step(call_log_id, next_step_id)
        else:
            # If no next step is found, end the call
            response = VoiceResponse()
            response.say("Thank you for your time. Goodbye.")
            response.hangup()
            return str(response)
        
    except Exception as e:
        logger.error(f"Error processing response: {str(e)}")
        return error_response()

@api_bp.route('/recordings', methods=['POST'])
def recording_callback():
    """
    Callback for Twilio recording status updates.
    """
    try:
        # Get the recording URL from the request
        recording_url = request.values.get('RecordingUrl')
        recording_sid = request.values.get('RecordingSid')
        call_sid = request.values.get('CallSid')
        
        logger.info(f"Recording callback: {recording_sid}, Call SID: {call_sid}")
        
        # Find the call log
        call_log = CallLog.query.filter_by(call_sid=call_sid).first()
        
        if call_log and recording_url:
            # Update the call log with the recording URL
            call_log.recording_url = recording_url
            db.session.commit()
        
        return '', 204
        
    except Exception as e:
        logger.error(f"Error in recording callback: {str(e)}")
        return '', 500

@api_bp.route('/campaign/<int:campaign_id>/start', methods=['POST'])
@login_required
def start_campaign(campaign_id):
    """
    Start a campaign.
    """
    # This would be implemented to start making calls for a campaign
    # In a real implementation, this would be a Celery task
    return jsonify({'success': True, 'message': 'Campaign started'})

@api_bp.route('/campaign/<int:campaign_id>/pause', methods=['POST'])
@login_required
def pause_campaign(campaign_id):
    """
    Pause a campaign.
    """
    # This would be implemented to pause making calls for a campaign
    return jsonify({'success': True, 'message': 'Campaign paused'})

def error_response():
    """
    Generate an error response.
    """
    response = VoiceResponse()
    response.say("We're sorry, but there was an error processing your call. Please try again later.")
    response.hangup()
    return str(response)
