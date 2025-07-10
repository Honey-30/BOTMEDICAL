"""
Healthcare Chatbot Application Package
"""

from .models import db, User, ChatSession, Symptom, SymptomCategory, HealthRecord, AdminLog

__version__ = "2.0.0"
__author__ = "Healthcare AI Team"
__email__ = "support@healthchatbot.com"

# Package metadata
__all__ = [
    'db',
    'User', 
    'ChatSession',
    'Symptom',
    'SymptomCategory',
    'HealthRecord',
    'AdminLog'
]
