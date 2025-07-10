"""
Enhanced Database Models for Healthcare Chatbot
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
import uuid
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model with authentication and profile management."""
    
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    
    # Medical information (encrypted)
    medical_history = db.Column(db.Text)  # JSON string of medical conditions
    allergies = db.Column(db.Text)  # JSON string of allergies
    medications = db.Column(db.Text)  # JSON string of current medications
    emergency_contact = db.Column(db.Text)  # JSON string of emergency contact info
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_confirmed_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    chat_sessions = db.relationship('ChatSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    health_reports = db.relationship('HealthReport', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, email, username, password, **kwargs):
        self.email = email.lower()
        self.username = username
        self.set_password(password)
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_medical_history(self):
        """Get medical history as Python object."""
        return json.loads(self.medical_history) if self.medical_history else []
    
    def set_medical_history(self, history):
        """Set medical history from Python object."""
        self.medical_history = json.dumps(history)
    
    def get_allergies(self):
        """Get allergies as Python object."""
        return json.loads(self.allergies) if self.allergies else []
    
    def set_allergies(self, allergies):
        """Set allergies from Python object."""
        self.allergies = json.dumps(allergies)
    
    def get_medications(self):
        """Get medications as Python object."""
        return json.loads(self.medications) if self.medications else []
    
    def set_medications(self, medications):
        """Set medications from Python object."""
        self.medications = json.dumps(medications)
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': str(self.id),
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class ChatSession(db.Model):
    """Chat session model to track user conversations."""
    
    __tablename__ = 'chat_sessions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    
    # Session metadata
    title = db.Column(db.String(200))
    status = db.Column(db.String(20), default='active')  # active, completed, archived
    
    # Conversation summary
    symptoms_identified = db.Column(db.Text)  # JSON array of symptoms
    conditions_discussed = db.Column(db.Text)  # JSON array of conditions
    emergency_flag = db.Column(db.Boolean, default=False)
    severity_level = db.Column(db.String(20))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    # Relationships
    messages = db.relationship('ChatMessage', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    health_report = db.relationship('HealthReport', backref='session', uselist=False, cascade='all, delete-orphan')
    
    def get_symptoms(self):
        """Get symptoms as Python list."""
        return json.loads(self.symptoms_identified) if self.symptoms_identified else []
    
    def set_symptoms(self, symptoms):
        """Set symptoms from Python list."""
        self.symptoms_identified = json.dumps(symptoms)
    
    def get_conditions(self):
        """Get conditions as Python list."""
        return json.loads(self.conditions_discussed) if self.conditions_discussed else []
    
    def set_conditions(self, conditions):
        """Set conditions from Python list."""
        self.conditions_discussed = json.dumps(conditions)
    
    def to_dict(self):
        """Convert session to dictionary."""
        return {
            'id': str(self.id),
            'title': self.title,
            'status': self.status,
            'symptoms': self.get_symptoms(),
            'conditions': self.get_conditions(),
            'emergency_flag': self.emergency_flag,
            'severity_level': self.severity_level,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': self.messages.count()
        }

class ChatMessage(db.Model):
    """Individual chat messages within a session."""
    
    __tablename__ = 'chat_messages'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(UUID(as_uuid=True), db.ForeignKey('chat_sessions.id'), nullable=False)
    
    # Message content
    message_type = db.Column(db.String(20), nullable=False)  # user, assistant, system
    content = db.Column(db.Text, nullable=False)
    
    # Metadata
    confidence_score = db.Column(db.Float)
    processing_time = db.Column(db.Float)  # Time taken to generate response
    model_version = db.Column(db.String(50))
    
    # Analysis results (for assistant messages)
    symptoms_extracted = db.Column(db.Text)  # JSON array
    predictions = db.Column(db.Text)  # JSON array of predictions
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def get_symptoms_extracted(self):
        """Get extracted symptoms as Python list."""
        return json.loads(self.symptoms_extracted) if self.symptoms_extracted else []
    
    def set_symptoms_extracted(self, symptoms):
        """Set extracted symptoms from Python list."""
        self.symptoms_extracted = json.dumps(symptoms)
    
    def get_predictions(self):
        """Get predictions as Python list."""
        return json.loads(self.predictions) if self.predictions else []
    
    def set_predictions(self, predictions):
        """Set predictions from Python list."""
        self.predictions = json.dumps(predictions)
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': str(self.id),
            'message_type': self.message_type,
            'content': self.content,
            'confidence_score': self.confidence_score,
            'symptoms_extracted': self.get_symptoms_extracted(),
            'predictions': self.get_predictions(),
            'created_at': self.created_at.isoformat()
        }

class HealthReport(db.Model):
    """Generated health reports for users."""
    
    __tablename__ = 'health_reports'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(UUID(as_uuid=True), db.ForeignKey('chat_sessions.id'), nullable=True)
    
    # Report content
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text)
    symptoms = db.Column(db.Text)  # JSON array
    predictions = db.Column(db.Text)  # JSON array
    recommendations = db.Column(db.Text)  # JSON array
    follow_up_questions = db.Column(db.Text)  # JSON array
    
    # Metadata
    report_type = db.Column(db.String(50))  # session_summary, periodic_report, emergency_alert
    severity_level = db.Column(db.String(20))
    emergency_flag = db.Column(db.Boolean, default=False)
    
    # File information
    pdf_path = db.Column(db.String(500))
    generated_by = db.Column(db.String(100))  # AI model version or human doctor
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert report to dictionary."""
        return {
            'id': str(self.id),
            'title': self.title,
            'summary': self.summary,
            'symptoms': json.loads(self.symptoms) if self.symptoms else [],
            'predictions': json.loads(self.predictions) if self.predictions else [],
            'recommendations': json.loads(self.recommendations) if self.recommendations else [],
            'severity_level': self.severity_level,
            'emergency_flag': self.emergency_flag,
            'created_at': self.created_at.isoformat()
        }

class SymptomKnowledge(db.Model):
    """Knowledge base for symptoms and their relationships."""
    
    __tablename__ = 'symptom_knowledge'
    
    id = db.Column(db.Integer, primary_key=True)
    symptom_name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Symptom information
    description = db.Column(db.Text)
    severity_weight = db.Column(db.Float, default=1.0)
    is_emergency = db.Column(db.Boolean, default=False)
    
    # Medical categorization
    body_system = db.Column(db.String(50))  # respiratory, cardiovascular, etc.
    symptom_type = db.Column(db.String(50))  # pain, fever, cognitive, etc.
    
    # Relationships
    aliases = db.Column(db.Text)  # JSON array of alternative names
    related_symptoms = db.Column(db.Text)  # JSON array of related symptoms
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_aliases(self):
        """Get aliases as Python list."""
        return json.loads(self.aliases) if self.aliases else []
    
    def get_related_symptoms(self):
        """Get related symptoms as Python list."""
        return json.loads(self.related_symptoms) if self.related_symptoms else []

class DiseaseKnowledge(db.Model):
    """Knowledge base for diseases and conditions."""
    
    __tablename__ = 'disease_knowledge'
    
    id = db.Column(db.Integer, primary_key=True)
    disease_name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Disease information
    description = db.Column(db.Text)
    severity_level = db.Column(db.String(20))  # mild, moderate, severe, critical
    prevalence = db.Column(db.String(50))  # common, uncommon, rare
    
    # Medical categorization
    category = db.Column(db.String(50))  # infectious, chronic, acute, etc.
    icd_10_code = db.Column(db.String(10))  # Medical classification code
    
    # Associated data
    common_symptoms = db.Column(db.Text)  # JSON array
    risk_factors = db.Column(db.Text)  # JSON array
    remedies = db.Column(db.Text)  # JSON array
    precautions = db.Column(db.Text)  # JSON array
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_common_symptoms(self):
        """Get common symptoms as Python list."""
        return json.loads(self.common_symptoms) if self.common_symptoms else []
    
    def get_remedies(self):
        """Get remedies as Python list."""
        return json.loads(self.remedies) if self.remedies else []
    
    def get_precautions(self):
        """Get precautions as Python list."""
        return json.loads(self.precautions) if self.precautions else []

class AuditLog(db.Model):
    """Audit log for tracking system actions and user activities."""
    
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    
    # Action details
    action = db.Column(db.String(100), nullable=False)  # login, prediction, report_generated, etc.
    resource_type = db.Column(db.String(50))  # user, session, report, etc.
    resource_id = db.Column(db.String(100))
    
    # Request details
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    endpoint = db.Column(db.String(200))
    
    # Metadata
    details = db.Column(db.Text)  # JSON string with additional details
    status = db.Column(db.String(20))  # success, error, warning
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert audit log to dictionary."""
        return {
            'id': self.id,
            'user_id': str(self.user_id) if self.user_id else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
