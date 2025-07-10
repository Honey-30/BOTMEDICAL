#!/usr/bin/env python3
"""
Simple startup script for the Healthcare Chatbot
"""

import os
import sys

def main():
    # Change to the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Add to Python path
    sys.path.insert(0, project_dir)
    
    print("🏥 Starting Healthcare Chatbot...")
    print(f"📁 Working directory: {project_dir}")
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import and run the application
        from run import main as run_main
        run_main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📦 Trying to install missing packages...")
        
        # Try to install minimal requirements
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "python-dotenv"])
            print("✅ Basic packages installed, retrying...")
            
            # Retry import
            from dotenv import load_dotenv
            load_dotenv()
            from run import main as run_main
            run_main()
            
        except Exception as install_error:
            print(f"❌ Could not install packages: {install_error}")
            
            # Fallback to minimal Flask app
            print("🔄 Starting minimal Flask application...")
            start_minimal_app()
    
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("🔄 Starting minimal Flask application...")
        start_minimal_app()

def start_minimal_app():
    """Start a minimal Flask application as fallback"""
    try:
        from flask import Flask, render_template, request, jsonify
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'dev-key'
        
        @app.route('/')
        def index():
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Healthcare Chatbot</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background-color: #f0f8ff; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                    h1 { color: #2c5aa0; text-align: center; }
                    .chat-area { border: 2px solid #ddd; height: 300px; padding: 10px; margin: 20px 0; overflow-y: auto; background-color: #fafafa; }
                    input[type="text"] { width: 70%; padding: 10px; margin-right: 10px; border: 1px solid #ddd; border-radius: 5px; }
                    button { padding: 10px 20px; background-color: #2c5aa0; color: white; border: none; border-radius: 5px; cursor: pointer; }
                    button:hover { background-color: #1e3d72; }
                    .message { margin: 10px 0; padding: 8px; border-radius: 5px; }
                    .user-message { background-color: #e3f2fd; text-align: right; }
                    .bot-message { background-color: #f1f8e9; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🏥 Healthcare Chatbot</h1>
                    <p><strong>Welcome to the AI Healthcare Chatbot!</strong></p>
                    <p>This is a simplified version. You can describe your symptoms and get basic health information.</p>
                    
                    <div id="chat-area" class="chat-area">
                        <div class="message bot-message">
                            <strong>Healthcare Bot:</strong> Hello! I'm your healthcare assistant. 
                            Please describe your symptoms, and I'll try to provide some general health information. 
                            <br><em>Note: This is for informational purposes only and should not replace professional medical advice.</em>
                        </div>
                    </div>
                    
                    <div>
                        <input type="text" id="user-input" placeholder="Describe your symptoms..." onkeypress="if(event.key==='Enter') sendMessage()">
                        <button onclick="sendMessage()">Send</button>
                    </div>
                </div>
                
                <script>
                    function sendMessage() {
                        const input = document.getElementById('user-input');
                        const message = input.value.trim();
                        if (!message) return;
                        
                        const chatArea = document.getElementById('chat-area');
                        
                        // Add user message
                        chatArea.innerHTML += `<div class="message user-message"><strong>You:</strong> ${message}</div>`;
                        
                        // Add bot response
                        const response = getResponse(message);
                        chatArea.innerHTML += `<div class="message bot-message"><strong>Healthcare Bot:</strong> ${response}</div>`;
                        
                        input.value = '';
                        chatArea.scrollTop = chatArea.scrollHeight;
                    }
                    
                    function getResponse(message) {
                        const msg = message.toLowerCase();
                        
                        if (msg.includes('fever') || msg.includes('temperature')) {
                            return 'Fever can be a sign of infection. Monitor your temperature, stay hydrated, and rest. If fever persists above 102°F (38.9°C) or lasts more than 3 days, consult a healthcare provider.';
                        } else if (msg.includes('headache')) {
                            return 'Headaches can have various causes including stress, dehydration, or tension. Try rest, hydration, and over-the-counter pain relievers. Seek medical attention for severe, sudden, or persistent headaches.';
                        } else if (msg.includes('cough')) {
                            return 'Coughs can be due to viral infections, allergies, or other causes. Stay hydrated, use honey for throat irritation, and consider a humidifier. See a doctor if cough persists over 2 weeks or is accompanied by fever.';
                        } else if (msg.includes('stomach') || msg.includes('nausea')) {
                            return 'Stomach issues can be caused by food, stress, or infections. Try bland foods (BRAT diet), stay hydrated, and rest. Seek medical care for severe pain, persistent vomiting, or signs of dehydration.';
                        } else if (msg.includes('tired') || msg.includes('fatigue')) {
                            return 'Fatigue can result from poor sleep, stress, or underlying conditions. Ensure adequate sleep, maintain a regular schedule, and eat well. Consult a doctor if fatigue persists or affects daily activities.';
                        } else {
                            return 'Thank you for sharing your symptoms. While I can provide general information, it\\'s important to consult with a healthcare professional for proper diagnosis and treatment. If you\\'re experiencing severe symptoms, please seek immediate medical attention.';
                        }
                    }
                </script>
            </body>
            </html>
            '''
        
        print("\n" + "=" * 60)
        print("🏥 Healthcare Chatbot - Minimal Version")
        print("=" * 60)
        print("🚀 Server starting on http://127.0.0.1:5000")
        print("🔧 This is a simplified version with basic functionality")
        print("📱 Open your browser and go to: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        
        app.run(host='127.0.0.1', port=5000, debug=True)
        
    except Exception as e:
        print(f"❌ Could not start minimal app: {e}")
        print("Please ensure Flask is installed: pip install flask")

if __name__ == '__main__':
    main()
