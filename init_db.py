import os
from flask import Flask
from models import db, User, Language, VoiceModel, ConversationFlow, VoterList, Campaign, CallLog, CallStep
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import random

# Load environment variables
load_dotenv()

# Create a minimal Flask app for database initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

def init_db():
    """Initialize the database with sample data"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if any users exist
        if User.query.count() == 0:
            print("Creating admin user...")
            admin = User(
                username="admin",
                email="admin@example.com",
                is_admin=True
            )
            admin.set_password("adminpassword")
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully.")
            print("You can now log in with:")
            print("Username: admin")
            print("Password: adminpassword")
        
        # Add basic languages
        if Language.query.count() == 0:
            print("Adding languages...")
            languages = [
                {"name": "English", "code": "en"},
                {"name": "Swahili", "code": "sw"},
                {"name": "Luganda", "code": "lg"},
                {"name": "Runyankole", "code": "nyn"}
            ]
            
            for lang_data in languages:
                language = Language(
                    name=lang_data['name'],
                    code=lang_data['code'],
                    is_active=True
                )
                db.session.add(language)
            
            db.session.commit()
            print(f"Added {len(languages)} languages.")
        
        # Add voice models
        if VoiceModel.query.count() == 0:
            print("Adding voice models...")
            voice_models = [
                {
                    "name": "Presidential Voice (English)",
                    "description": "Presidential candidate voice model for English language",
                    "file_path": "uploads/voice_models/presidential_en.model",
                    "sample_audio_path": "uploads/audio/sample_en.mp3",
                    "language_code": "en"
                },
                {
                    "name": "Presidential Voice (Luganda)",
                    "description": "Presidential candidate voice model for Luganda language",
                    "file_path": "uploads/voice_models/presidential_lg.model",
                    "sample_audio_path": "uploads/audio/sample_lg.mp3",
                    "language_code": "lg"
                },
                {
                    "name": "Presidential Voice (Swahili)",
                    "description": "Presidential candidate voice model for Swahili language",
                    "file_path": "uploads/voice_models/presidential_sw.model",
                    "sample_audio_path": "uploads/audio/sample_sw.mp3",
                    "language_code": "sw"
                }
            ]
            
            for model_data in voice_models:
                # Get language ID
                language = Language.query.filter_by(code=model_data['language_code']).first()
                if language:
                    model = VoiceModel(
                        name=model_data['name'],
                        description=model_data['description'],
                        file_path=model_data['file_path'],
                        sample_audio_path=model_data['sample_audio_path'],
                        is_active=True
                    )
                    db.session.add(model)
            
            db.session.commit()
            print(f"Added {len(voice_models)} voice models.")
        
        # Add conversation flows
        if ConversationFlow.query.count() == 0:
            print("Adding conversation flows...")
            flows = [
                {
                    "name": "Presidential Introduction",
                    "description": "Presidential candidate introduction and campaign platform overview.",
                    "flow_type": "informational",
                    "steps": [
                        {
                            "order": 0,
                            "content": "Hello, this is [Candidate Name]. I'm running for president in the upcoming election and wanted to personally reach out to you.",
                            "type": "message"
                        },
                        {
                            "order": 1,
                            "content": "My campaign is focused on economic growth, healthcare reform, and improving education across Uganda. I believe every citizen deserves opportunity and prosperity.",
                            "type": "message"
                        },
                        {
                            "order": 2,
                            "content": "I hope I can count on your support in the upcoming election. Would you like to learn more about my specific policy positions?",
                            "type": "question"
                        },
                        {
                            "order": 3,
                            "content": "Thank you for your time. Remember to vote on election day, [Election Date]. Together, we can build a better Uganda.",
                            "type": "message"
                        }
                    ]
                },
                {
                    "name": "Voter Registration",
                    "description": "Helps voters check registration status and provides polling location information.",
                    "flow_type": "interactive",
                    "steps": [
                        {
                            "order": 0,
                            "content": "Hello, this is [Candidate Name]'s campaign. We're calling to help ensure you're registered to vote in the upcoming election.",
                            "type": "message"
                        },
                        {
                            "order": 1,
                            "content": "Have you registered to vote for the upcoming election?",
                            "type": "question"
                        },
                        {
                            "order": 2,
                            "content": "Do you know where your polling station is located?",
                            "type": "question"
                        },
                        {
                            "order": 3,
                            "content": "The deadline for registration is [Registration Deadline]. You can register at any district office or online at [Registration Website].",
                            "type": "message"
                        },
                        {
                            "order": 4,
                            "content": "Thank you for your time. Please remember to vote on election day.",
                            "type": "message"
                        }
                    ]
                },
                {
                    "name": "Policy Q&A",
                    "description": "Answers common questions about candidate policy positions on key issues.",
                    "flow_type": "interactive",
                    "steps": [
                        {
                            "order": 0,
                            "content": "Hello, this is [Candidate Name]'s campaign. We're calling to discuss our policy positions and answer any questions you might have.",
                            "type": "message"
                        },
                        {
                            "order": 1,
                            "content": "What policy area are you most interested in learning about? Options include healthcare, education, economy, or infrastructure.",
                            "type": "question"
                        },
                        {
                            "order": 2,
                            "content": "Our healthcare plan includes expanding access to medical facilities in rural areas, reducing the cost of essential medications, and implementing a national health insurance program.",
                            "type": "message"
                        },
                        {
                            "order": 3,
                            "content": "Would you like to learn about another policy area?",
                            "type": "question"
                        },
                        {
                            "order": 4,
                            "content": "Thank you for your interest in our campaign. We hope we can count on your support.",
                            "type": "message"
                        }
                    ]
                }
            ]
            
            for flow_data in flows:
                flow = ConversationFlow(
                    name=flow_data['name'],
                    description=flow_data['description'],
                    is_active=True,
                    flow_data=json.dumps(flow_data['steps'])
                )
                db.session.add(flow)
            
            db.session.commit()
            print(f"Added {len(flows)} conversation flows.")
        
        # Add voter lists
        if VoterList.query.count() == 0:
            print("Adding voter lists...")
            voter_lists = [
                {
                    "name": "Kampala District Voters",
                    "description": "Primary voter list for Kampala district",
                    "region": "Kampala",
                    "file_path": "uploads/voter_data/kampala_voters.csv",
                    "total_numbers": 12450,
                    "valid_numbers": 8320
                },
                {
                    "name": "Eastern Region Voters",
                    "description": "Regional voter list for Eastern Uganda",
                    "region": "Eastern Uganda",
                    "file_path": "uploads/voter_data/eastern_voters.csv",
                    "total_numbers": 9845,
                    "valid_numbers": 6210
                },
                {
                    "name": "Youth Voters",
                    "description": "Young voters aged 18-35 nationwide",
                    "region": "Nationwide",
                    "file_path": "uploads/voter_data/youth_voters.csv",
                    "total_numbers": 15320,
                    "valid_numbers": 14850
                }
            ]
            
            for list_data in voter_lists:
                voter_list = VoterList(
                    name=list_data['name'],
                    description=list_data['description'],
                    file_path=list_data['file_path'],
                    total_numbers=list_data['total_numbers'],
                    valid_numbers=list_data['valid_numbers'],
                    is_active=True
                )
                db.session.add(voter_list)
            
            db.session.commit()
            print(f"Added {len(voter_lists)} voter lists.")
        
        # Add campaigns
        if Campaign.query.count() == 0:
            print("Adding campaigns...")
            campaigns = [
                {
                    "name": "Presidential Introduction Campaign",
                    "description": "Introducing the presidential candidate to voters",
                    "status": "active",
                    "max_calls_per_day": 1000,
                    "max_calls_per_hour": 100,
                    "conversation_flow_id": 1,  # Presidential Introduction
                    "voter_list_id": 1,  # Kampala District Voters
                    "start_date": datetime.now() - timedelta(days=5),
                    "end_date": datetime.now() + timedelta(days=25)
                },
                {
                    "name": "Voter Registration Reminder",
                    "description": "Reminding voters about registration deadlines",
                    "status": "active",
                    "max_calls_per_day": 1500,
                    "max_calls_per_hour": 150,
                    "conversation_flow_id": 2,  # Voter Registration
                    "voter_list_id": 2,  # Eastern Region Voters
                    "start_date": datetime.now() - timedelta(days=3),
                    "end_date": datetime.now() + timedelta(days=15)
                }
            ]
            
            for campaign_data in campaigns:
                campaign = Campaign(
                    name=campaign_data['name'],
                    description=campaign_data['description'],
                    status=campaign_data['status'],
                    max_calls_per_day=campaign_data['max_calls_per_day'],
                    max_calls_per_hour=campaign_data['max_calls_per_hour'],
                    conversation_flow_id=campaign_data['conversation_flow_id'],
                    voter_list_id=campaign_data['voter_list_id'],
                    start_date=campaign_data['start_date'],
                    end_date=campaign_data['end_date']
                )
                db.session.add(campaign)
            
            db.session.commit()
            print(f"Added {len(campaigns)} campaigns.")
        
        # Add call logs
        if CallLog.query.count() == 0:
            print("Adding call logs...")
            # Sample phone numbers
            phone_numbers = [
                "+256 701 234 567",
                "+256 772 345 678",
                "+256 712 456 789",
                "+256 782 567 890",
                "+256 703 678 901"
            ]
            
            # Sample statuses
            statuses = ["completed", "failed", "in-progress"]
            
            # Generate 50 sample call logs
            for i in range(50):
                # Randomly select status with weighted probability
                status = random.choices(
                    statuses, 
                    weights=[0.75, 0.15, 0.10],  # 75% completed, 15% failed, 10% in-progress
                    k=1
                )[0]
                
                # Set duration based on status
                if status == "completed":
                    duration = random.randint(60, 180)  # 1-3 minutes
                elif status == "in-progress":
                    duration = random.randint(10, 60)  # 10-60 seconds so far
                else:  # failed
                    duration = random.randint(0, 10)  # 0-10 seconds
                
                # Random time in the past 7 days
                time_offset = random.randint(0, 7 * 24 * 60 * 60)  # seconds in 7 days
                created_at = datetime.now() - timedelta(seconds=time_offset)
                
                # Random campaign ID (1 or 2)
                campaign_id = random.randint(1, 2)
                
                # Create call log
                call_log = CallLog(
                    call_sid=f"CA{i:08d}",
                    phone_number=random.choice(phone_numbers),
                    status=status,
                    duration=duration,
                    campaign_id=campaign_id,
                    voter_id=1,  # Placeholder, would normally be a real voter ID
                    created_at=created_at,
                    started_at=created_at,
                    ended_at=created_at + timedelta(seconds=duration) if status != "in-progress" else None
                )
                db.session.add(call_log)
            
            db.session.commit()
            print(f"Added 50 sample call logs.")
        
        print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
