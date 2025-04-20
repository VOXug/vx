import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_socketio import SocketIO
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['AUDIO_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'audio')
app.config['VOICE_MODELS_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'voice_models')
app.config['VOTER_DATA_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'voter_data')

# Ensure upload directories exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['AUDIO_FOLDER'], 
               app.config['VOICE_MODELS_FOLDER'], app.config['VOTER_DATA_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Import models after app initialization to avoid circular imports
from models import db, User, APIConfig, VoiceModel, Language, ConversationFlow, VoterList, Campaign, CallLog

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.voice import voice_bp
from routes.campaigns import campaigns_bp
from routes.languages import languages_bp
from routes.flows import flows_bp
from routes.voters import voters_bp
from routes.callcenter import callcenter_bp

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(voice_bp)
app.register_blueprint(campaigns_bp)
app.register_blueprint(languages_bp)
app.register_blueprint(flows_bp)
app.register_blueprint(voters_bp)
app.register_blueprint(callcenter_bp)

# Root route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))

# Demo route to show the system is working
@app.route('/demo')
def demo():
    return render_template('base_simple.html', title='Demo Page')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Create database tables
@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
