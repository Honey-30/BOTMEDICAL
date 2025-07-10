#!/usr/bin/env python3
"""
Simple starter script for AI Healthcare Chatbot
This script will set up and run the application with minimal dependencies
"""

import os
import sys
import subprocess
from pathlib import Path

# Get the project directory
PROJECT_DIR = Path(__file__).parent
VENV_DIR = PROJECT_DIR / "venv"
PYTHON_EXE = VENV_DIR / "Scripts" / "python.exe" if os.name == 'nt' else VENV_DIR / "bin" / "python"

def run_command(cmd, check=True):
    """Run a command and handle errors."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, cwd=PROJECT_DIR)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False

def setup_environment():
    """Set up the Python virtual environment and install dependencies."""
    print("Setting up AI Healthcare Chatbot environment...")
    
    # Check if Python is available
    if not run_command("python --version", check=False):
        print("❌ Python is not installed or not in PATH!")
        print("Please install Python 3.11+ from https://python.org")
        return False
    
    # Create virtual environment if it doesn't exist
    if not VENV_DIR.exists():
        print("📦 Creating virtual environment...")
        if not run_command("python -m venv venv"):
            return False
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':
        activate_script = VENV_DIR / "Scripts" / "activate.bat"
        pip_cmd = f'"{VENV_DIR / "Scripts" / "pip.exe"}"'
        python_cmd = f'"{PYTHON_EXE}"'
    else:
        activate_script = VENV_DIR / "bin" / "activate"
        pip_cmd = f'"{VENV_DIR / "bin" / "pip"}'
        python_cmd = f'"{PYTHON_EXE}"'
    
    print("📥 Installing dependencies...")
    if not run_command(f"{pip_cmd} install --upgrade pip"):
        return False
    
    if not run_command(f"{pip_cmd} install flask flask-sqlalchemy python-dotenv"):
        return False
    
    # Try to install full requirements if possible
    requirements_file = PROJECT_DIR / "requirements.txt"
    if requirements_file.exists():
        print("📋 Installing from requirements.txt...")
        run_command(f"{pip_cmd} install -r requirements.txt", check=False)
    
    return True

def create_minimal_app():
    """Create a minimal version of the app if the full version fails."""
    app_code = '''
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthcare_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Simple User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Simple ChatMessage model
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Healthcare Chatbot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            .chat-box { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 15px; margin: 20px 0; background: #fafafa; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user-message { background: #007bff; color: white; text-align: right; }
            .bot-message { background: #e9ecef; color: #333; }
            input[type="text"] { width: 70%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Healthcare Chatbot</h1>
            <p>Welcome to your personal health assistant!</p>
            
            <div class="chat-box" id="chatBox">
                <div class="message bot-message">
                    Hello! I'm your AI health assistant. You can ask me about symptoms, general health questions, or medical information. How can I help you today?
                </div>
            </div>
            
            <div>
                <input type="text" id="messageInput" placeholder="Type your health question here..." onkeypress="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">Send</button>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 5px;">
                <strong>⚠️ Disclaimer:</strong> This chatbot is for informational purposes only and should not replace professional medical advice. Always consult with qualified healthcare providers for medical decisions.
            </div>
        </div>

        <script>
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message) return;
                
                const chatBox = document.getElementById('chatBox');
                
                // Add user message
                const userDiv = document.createElement('div');
                userDiv.className = 'message user-message';
                userDiv.textContent = message;
                chatBox.appendChild(userDiv);
                
                // Clear input
                input.value = '';
                
                // Simulate bot response
                setTimeout(() => {
                    const botDiv = document.createElement('div');
                    botDiv.className = 'message bot-message';
                    botDiv.textContent = generateResponse(message);
                    chatBox.appendChild(botDiv);
                    chatBox.scrollTop = chatBox.scrollHeight;
                }, 1000);
                
                chatBox.scrollTop = chatBox.scrollHeight;
            }
            
            function generateResponse(message) {
                const responses = {
                    'headache': 'For headaches, try resting in a quiet, dark room. Stay hydrated and consider over-the-counter pain relievers if appropriate. If headaches persist or worsen, consult a healthcare provider.',
                    'fever': 'For fever, rest and stay hydrated. Monitor your temperature and consider fever-reducing medication if needed. Seek medical attention if fever is high (over 103°F) or persists.',
                    'cough': 'For a cough, stay hydrated, use a humidifier, and consider honey or throat lozenges. See a doctor if the cough persists for more than a few weeks or is accompanied by other concerning symptoms.',
                    'pain': 'Pain can have many causes. Rest, ice/heat therapy, and over-the-counter pain relievers may help. Consult a healthcare provider for persistent or severe pain.',
                    'emergency': '🚨 If this is a medical emergency, please call 911 immediately or go to your nearest emergency room.',
                    'help': 'I can help you with general health questions, symptom information, and wellness tips. What specific health concern do you have?'
                };
                
                const lowerMessage = message.toLowerCase();
                
                // Check for emergency keywords
                if (lowerMessage.includes('emergency') || lowerMessage.includes('911') || lowerMessage.includes('urgent')) {
                    return responses['emergency'];
                }
                
                // Check for specific symptoms
                for (const [keyword, response] of Object.entries(responses)) {
                    if (lowerMessage.includes(keyword)) {
                        return response;
                    }
                }
                
                // Default response
                return "Thank you for your question. While I can provide general health information, I recommend consulting with a healthcare professional for personalized medical advice. Is there a specific symptom or health topic you'd like to know more about?";
            }
        </script>
    </body>
    </html>
    """

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    message = data.get('message', '')
    
    # Simple response logic (can be enhanced with ML later)
    if 'emergency' in message.lower():
        response = "🚨 If this is a medical emergency, please call 911 immediately!"
    elif any(word in message.lower() for word in ['headache', 'pain', 'hurt']):
        response = "For pain management, rest and over-the-counter pain relievers may help. Consult a doctor if pain persists."
    elif any(word in message.lower() for word in ['fever', 'temperature', 'hot']):
        response = "For fever, rest and stay hydrated. Monitor temperature and seek medical attention if it's high or persistent."
    else:
        response = "Thank you for your question. I recommend consulting with a healthcare professional for personalized advice."
    
    # Save to database
    chat_message = ChatMessage(message=message, response=response)
    db.session.add(chat_message)
    db.session.commit()
    
    return jsonify({'response': response})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("🚀 Starting AI Healthcare Chatbot...")
    print("💻 Open your browser and go to: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)
'''
    
    # Write the minimal app
    minimal_app_file = PROJECT_DIR / "minimal_app.py"
    with open(minimal_app_file, 'w') as f:
        f.write(app_code)
    
    return minimal_app_file

def main():
    """Main function to set up and run the application."""
    print("🏥 AI Healthcare Chatbot Setup")
    print("=" * 40)
    
    # Setup environment
    if not setup_environment():
        print("❌ Failed to set up environment. Trying minimal version...")
        minimal_app = create_minimal_app()
        print(f"✅ Created minimal app: {minimal_app}")
        print("Run with: python minimal_app.py")
        return
    
    # Try to run the full application
    print("🚀 Starting AI Healthcare Chatbot...")
    
    if os.name == 'nt':
        python_cmd = f'"{PYTHON_EXE}"'
    else:
        python_cmd = f'"{PYTHON_EXE}"'
    
    # First try the advanced application
    try:
        run_py = PROJECT_DIR / "run.py"
        if run_py.exists():
            print("🔧 Trying advanced application...")
            if run_command(f"{python_cmd} run.py", check=False):
                return
    except:
        pass
    
    # Fallback to minimal application
    print("📱 Starting minimal application...")
    minimal_app = create_minimal_app()
    run_command(f"{python_cmd} {minimal_app}")

if __name__ == "__main__":
    main()
