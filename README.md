# Real-Time Multilingual Conversational Voice AI Campaign System

A secure, full-stack AI-powered system for Uganda's Presidential Election that calls voters, talks to them in real-time using a cloned presidential voice, listens to their responses, understands them using GPT-4, and responds accordingly in their preferred language (English, Swahili, Luganda, or Runyankole).

## 🧠 Core Features

### 🔐 Admin Dashboard (Web Panel)
- Secure login system
- API configuration management (Twilio, GPT-4)
- Voice model training with OpenVoice
- Multilingual support
- Conversation flow builder with sentiment branching
- Voter list management
- Campaign scheduling and monitoring

### 🗣️ Voice AI & Audio Engine
- Voice cloning with OpenVoice
- Automatic audio generation in multiple languages
- Audio preview and regeneration
- Organized audio storage

### 🤖 Conversational AI Calling Engine
- Twilio-powered outbound calling
- Real-time speech-to-text with Whisper
- Language detection and sentiment analysis with GPT-4
- Dynamic response selection
- Comprehensive call logging

### 📊 Reports & Live Monitoring
- Real-time dashboard
- Filterable call logs
- Exportable reports (PDF, Excel)
- Analytics (call totals, engagement, sentiment, language distribution)

## 🧱 Technology Stack

- **Backend**: Python (Flask)
- **Frontend**: TailwindCSS
- **Voice Cloning**: OpenVoice
- **Speech Recognition**: Whisper
- **AI Understanding**: GPT-4
- **Telephony**: Twilio Programmable Voice
- **Database**: SQLite
- **Task Queue**: Celery with Redis
- **Deployment**: Docker, Nginx, Certbot

## 📋 Setup Instructions

### Prerequisites
- Docker and Docker Compose
- Twilio account with Programmable Voice
- OpenAI API key
- OpenVoice setup (or alternative voice cloning service)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/VOXug/vx.git
   cd vx
   ```

2. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file with your API keys and configuration.

4. Build and start the Docker containers:
   ```
   docker-compose up -d
   ```

5. Access the application at http://localhost:5000

### Initial Setup

1. Register an admin account (first user is automatically an admin)
2. Configure API keys in the Admin Dashboard
3. Add supported languages
4. Upload and train voice models
5. Create conversation flows
6. Upload voter lists
7. Create and schedule campaigns

## 📱 Usage Guide

### Voice Model Training
1. Navigate to Voice Models > Add Voice Model
2. Upload high-quality WAV or MP3 samples of the president's voice
3. Name the model and submit for training
4. Wait for training to complete
5. Generate a test sample to verify quality

### Conversation Flow Creation
1. Navigate to Conversation Flows > Add Flow
2. Create a basic flow with intro, talking points, and outro
3. Add branching based on voter sentiment
4. Test the flow with the preview feature

### Campaign Management
1. Navigate to Campaigns > Add Campaign
2. Select a conversation flow and voter list
3. Configure call limits and retry settings
4. Schedule the campaign start and end dates
5. Activate the campaign when ready

### Monitoring and Reporting
1. View real-time statistics on the Dashboard
2. Check detailed call logs in the Reports section
3. Export data for external analysis
4. View analytics charts for insights

## 🔒 Security Considerations

- All API keys are stored securely in the database
- User passwords are hashed using bcrypt
- HTTPS is enforced in production
- Do Not Call list is strictly enforced
- Call recordings are optional and require consent

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- Twilio for telephony services
- OpenAI for GPT-4 and Whisper
- OpenVoice for voice cloning technology
- Flask and SQLAlchemy for the web framework
- TailwindCSS for the UI components

DAX +256778415709 OR +256702448951
