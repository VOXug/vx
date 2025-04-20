import os
import logging
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from flask import current_app, url_for
from models import db, Campaign, CallLog, Voter, CallStep

# Set up logging
logger = logging.getLogger(__name__)

def get_twilio_client():
    """
    Get a Twilio client using the API credentials from the environment.
    
    Returns:
        twilio.rest.Client: A Twilio client instance
    """
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        logger.error("Twilio credentials not found in environment variables")
        return None
    
    return Client(account_sid, auth_token)

def make_call(phone_number, campaign_id, test=False):
    """
    Make a call to a voter using Twilio.
    
    Args:
        phone_number (str): The phone number to call
        campaign_id (int): The ID of the campaign
        test (bool): Whether this is a test call
        
    Returns:
        str: The Twilio call SID if successful, None otherwise
    """
    try:
        client = get_twilio_client()
        if not client:
            logger.error("Failed to initialize Twilio client")
            return None
        
        # Get the campaign
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            logger.error(f"Campaign with ID {campaign_id} not found")
            return None
        
        # Get the voter
        voter = Voter.query.filter_by(phone_number=phone_number).first()
        if not voter:
            # Create a new voter record
            voter = Voter(phone_number=phone_number)
            db.session.add(voter)
            db.session.commit()
        
        # Check if the voter is on the do not call list
        if voter.do_not_call:
            logger.warning(f"Voter {phone_number} is on the do not call list")
            return None
        
        # Create a call log
        call_log = CallLog(
            phone_number=phone_number,
            status='initiated',
            campaign_id=campaign.id,
            voter_id=voter.id
        )
        db.session.add(call_log)
        db.session.commit()
        
        # Get the Twilio caller number from environment
        caller_number = os.environ.get('TWILIO_CALLER_NUMBER')
        if not caller_number:
            logger.error("Twilio caller number not found in environment variables")
            return None
        
        # Make the call
        call = client.calls.create(
            to=phone_number,
            from_=caller_number,
            url=url_for('api.call_webhook', _external=True),
            status_callback=url_for('api.call_status_callback', call_log_id=call_log.id, _external=True),
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            status_callback_method='POST'
        )
        
        # Update the call log with the call SID
        call_log.call_sid = call.sid
        call_log.started_at = db.func.now()
        db.session.commit()
        
        logger.info(f"Call initiated to {phone_number}, Call SID: {call.sid}")
        return call.sid
        
    except Exception as e:
        logger.error(f"Error making call to {phone_number}: {str(e)}")
        return None

def generate_twiml_for_step(call_log_id, step_id=None):
    """
    Generate TwiML for a conversation step.
    
    Args:
        call_log_id (int): The ID of the call log
        step_id (str, optional): The ID of the step to generate TwiML for
        
    Returns:
        str: The TwiML response
    """
    try:
        # Get the call log
        call_log = CallLog.query.get(call_log_id)
        if not call_log:
            logger.error(f"Call log with ID {call_log_id} not found")
            return error_twiml()
        
        # Get the campaign
        campaign = Campaign.query.get(call_log.campaign_id)
        if not campaign:
            logger.error(f"Campaign with ID {call_log.campaign_id} not found")
            return error_twiml()
        
        # Get the conversation flow
        flow = campaign.conversation_flow
        if not flow:
            logger.error(f"Conversation flow not found for campaign {campaign.id}")
            return error_twiml()
        
        # Get the flow data
        flow_data = flow.get_flow_data()
        
        # If no step_id is provided, start with the first step
        if not step_id:
            step_id = flow_data['steps'][0]['id']
        
        # Find the step in the flow
        step = next((s for s in flow_data['steps'] if s['id'] == step_id), None)
        if not step:
            logger.error(f"Step {step_id} not found in flow {flow.id}")
            return error_twiml()
        
        # Create a new call step record
        call_step = CallStep(
            step_name=step['name'],
            call_log_id=call_log.id
        )
        db.session.add(call_step)
        db.session.commit()
        
        # Generate TwiML based on the step type
        response = VoiceResponse()
        
        if step['type'] == 'message':
            # Play the audio for this step
            # In a real implementation, you would get the audio clip for this step
            # For now, we'll just use <Say>
            response.say(step['text'])
            
            # If there's a next step, redirect to it
            if 'next' in step and step['next'] != 'end':
                response.redirect(url_for('api.call_step', call_log_id=call_log.id, step_id=step['next'], _external=True))
            else:
                response.hangup()
        
        elif step['type'] == 'response':
            # Use Gather to collect user input
            gather = Gather(
                input='speech',
                action=url_for('api.process_response', call_log_id=call_log.id, step_id=step_id, _external=True),
                method='POST',
                speechTimeout='auto',
                language='en-US'  # This would be dynamic based on detected language
            )
            
            # In a real implementation, you would play a prompt
            gather.say("Please share your thoughts.")
            
            response.append(gather)
            
            # If no input is received, try again or move to the next step
            response.redirect(url_for('api.call_step', call_log_id=call_log.id, step_id=step_id, _external=True))
        
        elif step['type'] == 'end':
            response.hangup()
        
        return str(response)
        
    except Exception as e:
        logger.error(f"Error generating TwiML for step {step_id}: {str(e)}")
        return error_twiml()

def error_twiml():
    """
    Generate an error TwiML response.
    
    Returns:
        str: The TwiML response
    """
    response = VoiceResponse()
    response.say("We're sorry, but there was an error processing your call. Please try again later.")
    response.hangup()
    return str(response)

def process_voter_response(call_log_id, step_id, response_text):
    """
    Process a voter's response using GPT-4.
    
    Args:
        call_log_id (int): The ID of the call log
        step_id (str): The ID of the step
        response_text (str): The voter's response text
        
    Returns:
        tuple: (next_step_id, sentiment, language)
    """
    try:
        # Get the call log
        call_log = CallLog.query.get(call_log_id)
        if not call_log:
            logger.error(f"Call log with ID {call_log_id} not found")
            return None, None, None
        
        # Get the campaign
        campaign = Campaign.query.get(call_log.campaign_id)
        if not campaign:
            logger.error(f"Campaign with ID {call_log.campaign_id} not found")
            return None, None, None
        
        # Get the conversation flow
        flow = campaign.conversation_flow
        if not flow:
            logger.error(f"Conversation flow not found for campaign {campaign.id}")
            return None, None, None
        
        # Get the flow data
        flow_data = flow.get_flow_data()
        
        # Find the step in the flow
        step = next((s for s in flow_data['steps'] if s['id'] == step_id), None)
        if not step:
            logger.error(f"Step {step_id} not found in flow {flow.id}")
            return None, None, None
        
        # Update the call step with the user's response
        call_step = CallStep.query.filter_by(call_log_id=call_log.id, step_name=step['name']).order_by(CallStep.timestamp.desc()).first()
        if call_step:
            call_step.user_response = response_text
            db.session.commit()
        
        # In a real implementation, you would use GPT-4 to analyze the response
        # For now, we'll just simulate it
        
        # Detect language (simplified)
        language = 'en'  # Default to English
        if 'swahili' in response_text.lower() or 'jambo' in response_text.lower():
            language = 'sw'
        elif 'luganda' in response_text.lower():
            language = 'lg'
        elif 'runyankole' in response_text.lower():
            language = 'nyn'
        
        # Detect sentiment (simplified)
        sentiment = 'neutral'
        positive_words = ['yes', 'good', 'great', 'excellent', 'support', 'like', 'agree']
        negative_words = ['no', 'bad', 'poor', 'terrible', 'oppose', 'dislike', 'disagree']
        
        if any(word in response_text.lower() for word in positive_words):
            sentiment = 'positive'
        elif any(word in response_text.lower() for word in negative_words):
            sentiment = 'negative'
        
        # Update the call step with the detected language and sentiment
        if call_step:
            call_step.language_detected = language
            call_step.sentiment = sentiment
            db.session.commit()
        
        # Update the call log with the detected language and sentiment
        call_log.detected_language = language
        call_log.sentiment = sentiment
        db.session.commit()
        
        # Determine the next step based on the sentiment
        next_step_id = None
        if 'branches' in step:
            next_step_id = step['branches'].get(sentiment, step['branches'].get('neutral'))
        
        return next_step_id, sentiment, language
        
    except Exception as e:
        logger.error(f"Error processing voter response: {str(e)}")
        return None, None, None
