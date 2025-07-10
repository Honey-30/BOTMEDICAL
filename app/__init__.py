"""
Healthcare Chatbot Application Package
"""

try:
    from .models import db, User, ChatSession, ChatMessage, HealthReport, AuditLog
    MODELS_AVAILABLE = True
except ImportError:
    # Handle missing dependencies gracefully
    MODELS_AVAILABLE = False
    db = None

__version__ = "2.0.0"
__author__ = "Healthcare AI Team"
__email__ = "support@healthchatbot.com"

# Package metadata
if MODELS_AVAILABLE:
    __all__ = [
        'db',
        'User', 
        'ChatSession',
        'ChatMessage',
        'HealthReport',
        'AuditLog'
    ]
else:
    __all__ = []

def create_app(config_name='development'):
    """Create and configure the Flask application."""
    try:
        from flask import Flask
        from config import config
        
        app = Flask(__name__)
        app.config.from_object(config[config_name])
        
        # Initialize extensions
        if MODELS_AVAILABLE and db:
            db.init_app(app)
        
        return app
    except ImportError:
        # Return a minimal Flask app for testing
        from flask import Flask
        app = Flask(__name__)
        app.config.update({
            'SECRET_KEY': 'test-secret-key',
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        })
        return app
