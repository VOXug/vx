import os
import logging
import openai
import tempfile
import requests
from flask import current_app

# Set up logging
logger = logging.getLogger(__name__)

def get_openai_client():
    """
    Initialize the OpenAI client with the API key from environment variables.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        return False
    
    openai.api_key = api_key
    return True

def transcribe_audio(audio_url):
    """
    Transcribe audio using OpenAI Whisper API.
    
    Args:
        audio_url (str): URL to the audio file to transcribe
        
    Returns:
        tuple: (transcription, language) or (None, None) if transcription failed
    """
    try:
        if not get_openai_client():
            return None, None
        
        # Download the audio file
        response = requests.get(audio_url)
        if response.status_code != 200:
            logger.error(f"Failed to download audio file from {audio_url}")
            return None, None
        
        # Save the audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe the audio
            with open(temp_file_path, 'rb') as audio_file:
                result = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            # Extract the transcription and language
            transcription = result.get('text', '')
            language = result.get('language', '')
            
            logger.info(f"Transcription successful. Language: {language}")
            return transcription, language
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        return None, None

def analyze_response(text, language=None):
    """
    Analyze a voter's response using GPT-4.
    
    Args:
        text (str): The text to analyze
        language (str, optional): The detected language of the text
        
    Returns:
        dict: Analysis results including sentiment, language, and key points
    """
    try:
        if not get_openai_client():
            return None
        
        # Prepare the prompt
        prompt = f"""
        Analyze the following voter response in the context of a political campaign call:
        
        "{text}"
        
        Provide the following information:
        1. Sentiment (positive, neutral, or negative)
        2. Language (if not provided, detect the language)
        3. Key points or concerns mentioned
        4. Recommended response approach
        
        Format your response as JSON.
        """
        
        # Call GPT-4
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant analyzing voter responses for a political campaign."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        # Extract the analysis
        analysis = response.choices[0].message.content
        
        # Parse the JSON response
        import json
        try:
            analysis_json = json.loads(analysis)
            return analysis_json
        except json.JSONDecodeError:
            logger.error("Failed to parse GPT-4 response as JSON")
            
            # Fallback to simple sentiment analysis
            sentiment = "neutral"
            if "yes" in text.lower() or "support" in text.lower() or "agree" in text.lower():
                sentiment = "positive"
            elif "no" in text.lower() or "against" in text.lower() or "disagree" in text.lower():
                sentiment = "negative"
            
            return {
                "sentiment": sentiment,
                "language": language or "en",
                "key_points": [],
                "recommended_response": "Thank the voter for their feedback."
            }
        
    except Exception as e:
        logger.error(f"Error analyzing response with GPT-4: {str(e)}")
        
        # Fallback to simple sentiment analysis
        sentiment = "neutral"
        if "yes" in text.lower() or "support" in text.lower() or "agree" in text.lower():
            sentiment = "positive"
        elif "no" in text.lower() or "against" in text.lower() or "disagree" in text.lower():
            sentiment = "negative"
        
        return {
            "sentiment": sentiment,
            "language": language or "en",
            "key_points": [],
            "recommended_response": "Thank the voter for their feedback."
        }
