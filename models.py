from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class APIConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    key = db.Column(db.String(256), nullable=False)
    value = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<APIConfig {self.name}>'

class VoiceModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(256), nullable=False)  # Path to the trained model
    sample_audio_path = db.Column(db.String(256))  # Path to a sample audio using this voice
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    audio_clips = db.relationship('AudioClip', backref='voice_model', lazy=True)
    
    def __repr__(self):
        return f'<VoiceModel {self.name}>'

class Language(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(10), nullable=False, unique=True)  # e.g., 'en', 'sw', 'lg', 'nyn'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    audio_clips = db.relationship('AudioClip', backref='language', lazy=True)
    
    def __repr__(self):
        return f'<Language {self.name}>'

class ConversationFlow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    flow_data = db.Column(db.Text, nullable=False)  # JSON string of the flow
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaigns = db.relationship('Campaign', backref='conversation_flow', lazy=True)
    
    def get_flow_data(self):
        return json.loads(self.flow_data)
    
    def set_flow_data(self, data):
        self.flow_data = json.dumps(data)
    
    def __repr__(self):
        return f'<ConversationFlow {self.name}>'

class AudioClip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    file_path = db.Column(db.String(256), nullable=False)
    text_content = db.Column(db.Text, nullable=False)  # The text that was converted to audio
    flow_step = db.Column(db.String(64))  # Which step in the conversation flow this belongs to
    sentiment = db.Column(db.String(20))  # 'positive', 'neutral', 'negative'
    duration = db.Column(db.Float)  # Duration in seconds
    
    # Foreign keys
    voice_model_id = db.Column(db.Integer, db.ForeignKey('voice_model.id'), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AudioClip {self.name}>'

class VoterList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(256), nullable=False)  # Path to the uploaded file
    total_numbers = db.Column(db.Integer, default=0)
    valid_numbers = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    campaigns = db.relationship('Campaign', backref='voter_list', lazy=True)
    
    def __repr__(self):
        return f'<VoterList {self.name}>'

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False, unique=True)
    do_not_call = db.Column(db.Boolean, default=False)
    region = db.Column(db.String(64))
    preferred_language_id = db.Column(db.Integer, db.ForeignKey('language.id'))
    
    # Relationships
    preferred_language = db.relationship('Language')
    call_logs = db.relationship('CallLog', backref='voter', lazy=True)
    
    def __repr__(self):
        return f'<Voter {self.phone_number}>'

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, active, paused, completed
    max_calls_per_day = db.Column(db.Integer, default=1000)
    max_calls_per_hour = db.Column(db.Integer, default=100)
    retry_attempts = db.Column(db.Integer, default=3)
    retry_delay_minutes = db.Column(db.Integer, default=60)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    # Foreign keys
    conversation_flow_id = db.Column(db.Integer, db.ForeignKey('conversation_flow.id'), nullable=False)
    voter_list_id = db.Column(db.Integer, db.ForeignKey('voter_list.id'), nullable=False)
    
    # Relationships
    call_logs = db.relationship('CallLog', backref='campaign', lazy=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Campaign {self.name}>'

class CallLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_sid = db.Column(db.String(64), unique=True)  # Twilio call SID
    phone_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # initiated, ringing, in-progress, completed, failed, busy, no-answer
    duration = db.Column(db.Integer)  # Duration in seconds
    recording_url = db.Column(db.String(256))  # URL to the call recording if available
    transcript = db.Column(db.Text)  # Full conversation transcript
    detected_language = db.Column(db.String(10))  # Detected language code
    sentiment = db.Column(db.String(20))  # Overall sentiment: positive, neutral, negative
    
    # Foreign keys
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'), nullable=False)
    
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    call_steps = db.relationship('CallStep', backref='call_log', lazy=True)
    
    def __repr__(self):
        return f'<CallLog {self.call_sid}>'

class CallStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    step_name = db.Column(db.String(64), nullable=False)  # e.g., 'intro', 'question1', 'response1'
    audio_played = db.Column(db.String(256))  # Path to the audio file played
    user_response = db.Column(db.Text)  # Transcribed user response
    sentiment = db.Column(db.String(20))  # Sentiment of this specific step
    language_detected = db.Column(db.String(10))  # Language detected in this step
    
    # Foreign keys
    call_log_id = db.Column(db.Integer, db.ForeignKey('call_log.id'), nullable=False)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CallStep {self.step_name}>'

class DoNotCallList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False, unique=True)
    reason = db.Column(db.String(256))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DoNotCallList {self.phone_number}>'
