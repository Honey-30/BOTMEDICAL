"""
Enhanced API Blueprint for Healthcare Chatbot
"""

from flask import Blueprint, request, jsonify, current_app, g
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, ValidationError
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..models import db, ChatSession, ChatMessage, HealthReport, AuditLog
from ..ml.advanced_models import AdvancedSymptomChecker, PredictionResult, SymptomAnalysis
from ..ml.nlp_processor import AdvancedMedicalNLP
from ..utils.security import require_api_key, log_api_access
from ..utils.cache import cache_response, get_cached_response
from ..utils.validators import validate_symptom_input, sanitize_input

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/1"
)

# Initialize ML models (would be done in app factory in production)
symptom_checker = None
nlp_processor = None

def init_ml_models(config: Dict[str, Any]):
    """Initialize ML models with configuration."""
    global symptom_checker, nlp_processor
    symptom_checker = AdvancedSymptomChecker(config)
    nlp_processor = AdvancedMedicalNLP(config)
    
    # Load pre-trained models
    try:
        symptom_checker.load_models()
        logger.info("ML models initialized successfully")
    except Exception as e:
        logger.warning(f"Could not load pre-trained models: {e}")

# Marshmallow Schemas for Input Validation
class SymptomInputSchema(Schema):
    """Schema for symptom input validation."""
    message = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    session_id = fields.Str(required=False)
    user_profile = fields.Dict(required=False)
    context = fields.Dict(required=False)

class FeedbackSchema(Schema):
    """Schema for feedback input validation."""
    prediction_id = fields.Str(required=True)
    rating = fields.Int(required=True, validate=lambda x: 1 <= x <= 5)
    comment = fields.Str(required=False)
    is_helpful = fields.Bool(required=True)

class ReportRequestSchema(Schema):
    """Schema for health report request validation."""
    session_id = fields.Str(required=True)
    report_type = fields.Str(required=False, validate=lambda x: x in ['summary', 'detailed', 'emergency'])
    include_recommendations = fields.Bool(required=False, default=True)

# Error Handlers
@api_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle marshmallow validation errors."""
    return jsonify({
        'error': 'Validation Error',
        'message': 'Invalid input data',
        'details': error.messages
    }), 400

@api_bp.errorhandler(429)
def handle_rate_limit_error(error):
    """Handle rate limit errors."""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'retry_after': error.retry_after
    }), 429

# Health Check Endpoint
@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'models_loaded': symptom_checker is not None and nlp_processor is not None
    })

# Symptom Analysis Endpoint
@api_bp.route('/analyze-symptoms', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
@log_api_access
def analyze_symptoms():
    """
    Analyze symptoms and provide predictions.
    
    Expected JSON payload:
    {
        "message": "I have a headache and fever",
        "session_id": "optional-session-id",
        "user_profile": {
            "age": 30,
            "gender": "male",
            "medical_history": ["hypertension"]
        }
    }
    """
    start_time = time.time()
    
    try:
        # Validate input
        schema = SymptomInputSchema()
        data = schema.load(request.json)
        
        # Sanitize input
        message = sanitize_input(data['message'])
        user_profile = data.get('user_profile', {})
        context = data.get('context', {})
        
        # Check cache first
        cache_key = f"symptoms:{current_user.id}:{hash(message)}"
        cached_result = get_cached_response(cache_key)
        if cached_result:
            return cached_result
        
        # Get or create chat session
        session = get_or_create_session(data.get('session_id'))
        
        # Extract symptoms using NLP
        extracted_symptoms = nlp_processor.extract_symptoms(message, context)
        
        # Analyze symptoms
        symptom_analysis = nlp_processor.analyze_symptoms(
            [s.normalized_text for s in extracted_symptoms],
            user_profile
        )
        
        # Get predictions
        predictions = symptom_checker.predict_with_confidence(
            [s.normalized_text for s in extracted_symptoms],
            user_profile
        )
        
        # Analyze sentiment
        sentiment_analysis = nlp_processor.analyze_sentiment(message)
        
        # Save chat message
        chat_message = ChatMessage(
            session_id=session.id,
            message_type='user',
            content=message,
            processing_time=time.time() - start_time,
            model_version='v1.0'
        )
        chat_message.set_symptoms_extracted([s.normalized_text for s in extracted_symptoms])
        chat_message.set_predictions([(p.disease, p.probability) for p in predictions])
        
        db.session.add(chat_message)
        
        # Update session
        session.set_symptoms(list(set(session.get_symptoms() + [s.normalized_text for s in extracted_symptoms])))
        session.emergency_flag = symptom_analysis.emergency_flag
        session.severity_level = symptom_analysis.severity_level
        session.updated_at = datetime.utcnow()
        
        # Generate response
        response_data = {
            'analysis': {
                'symptoms_extracted': [
                    {
                        'original': s.original_text,
                        'normalized': s.normalized_text,
                        'confidence': s.confidence,
                        'severity_indicators': s.severity_indicators,
                        'temporal_indicators': s.temporal_indicators,
                        'location_indicators': s.location_indicators
                    } for s in extracted_symptoms
                ],
                'severity': {
                    'score': symptom_analysis.severity_score,
                    'level': symptom_analysis.severity_level
                },
                'emergency_flag': symptom_analysis.emergency_flag,
                'body_systems_affected': symptom_analysis.body_systems_affected,
                'sentiment': sentiment_analysis
            },
            'predictions': [
                {
                    'disease': p.disease,
                    'probability': p.probability,
                    'confidence': p.confidence,
                    'risk_level': p.risk_level,
                    'recommendations': p.recommendations,
                    'follow_up_questions': p.follow_up
                } for p in predictions
            ],
            'session': {
                'id': str(session.id),
                'symptoms_history': session.get_symptoms(),
                'emergency_flag': session.emergency_flag
            },
            'metadata': {
                'processing_time': time.time() - start_time,
                'model_version': 'v1.0',
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        # Generate assistant response
        assistant_response = generate_assistant_response(
            symptom_analysis, predictions, sentiment_analysis
        )
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session.id,
            message_type='assistant',
            content=assistant_response,
            confidence_score=predictions[0].probability if predictions else 0.0
        )
        
        db.session.add(assistant_message)
        db.session.commit()
        
        response_data['response'] = assistant_response
        
        # Cache the response
        cache_response(cache_key, response_data, timeout=300)  # 5 minutes
        
        # Log the interaction
        audit_log = AuditLog(
            user_id=current_user.id,
            action='symptom_analysis',
            resource_type='chat_session',
            resource_id=str(session.id),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            endpoint=request.endpoint,
            status='success'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify(response_data)
        
    except ValidationError as e:
        logger.warning(f"Validation error in analyze_symptoms: {e.messages}")
        return jsonify({
            'error': 'Invalid input',
            'message': str(e.messages)
        }), 400
        
    except Exception as e:
        logger.error(f"Error in analyze_symptoms: {str(e)}", exc_info=True)
        
        # Log the error
        audit_log = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action='symptom_analysis',
            resource_type='error',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            endpoint=request.endpoint,
            status='error',
            details=str(e)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred while processing your request'
        }), 500

# Follow-up Questions Endpoint
@api_bp.route('/follow-up-questions', methods=['POST'])
@limiter.limit("20 per minute")
@login_required
def get_follow_up_questions():
    """Get follow-up questions based on current analysis."""
    try:
        data = request.json
        session_id = data.get('session_id')
        disease = data.get('disease')
        
        if not session_id or not disease:
            return jsonify({
                'error': 'Missing required parameters',
                'message': 'session_id and disease are required'
            }), 400
        
        session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if not session:
            return jsonify({
                'error': 'Session not found',
                'message': 'Invalid session ID'
            }), 404
        
        # Generate follow-up questions
        symptoms = session.get_symptoms()
        questions = nlp_processor.get_follow_up_questions(disease, symptoms)
        
        return jsonify({
            'questions': questions,
            'disease': disease,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error getting follow-up questions: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Could not generate follow-up questions'
        }), 500

# Health Report Generation
@api_bp.route('/generate-report', methods=['POST'])
@limiter.limit("5 per hour")
@login_required
def generate_health_report():
    """Generate a comprehensive health report."""
    try:
        schema = ReportRequestSchema()
        data = schema.load(request.json)
        
        session_id = data['session_id']
        report_type = data.get('report_type', 'summary')
        include_recommendations = data.get('include_recommendations', True)
        
        # Get session
        session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if not session:
            return jsonify({
                'error': 'Session not found',
                'message': 'Invalid session ID'
            }), 404
        
        # Generate report
        report = create_health_report(session, report_type, include_recommendations)
        
        return jsonify({
            'report': report.to_dict(),
            'download_url': f'/api/v1/reports/{report.id}/download'
        })
        
    except ValidationError as e:
        return jsonify({
            'error': 'Invalid input',
            'message': str(e.messages)
        }), 400
        
    except Exception as e:
        logger.error(f"Error generating health report: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Could not generate health report'
        }), 500

# Symptom Suggestions for Autocomplete
@api_bp.route('/symptom-suggestions', methods=['GET'])
@limiter.limit("100 per minute")
def get_symptom_suggestions():
    """Get symptom suggestions for autocomplete."""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 20)
        
        if len(query) < 2:
            return jsonify({'suggestions': []})
        
        suggestions = nlp_processor.get_symptom_suggestions(query, limit)
        
        return jsonify({
            'suggestions': suggestions,
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Error getting symptom suggestions: {str(e)}")
        return jsonify({'suggestions': []})

# User Feedback
@api_bp.route('/feedback', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
def submit_feedback():
    """Submit feedback on predictions."""
    try:
        schema = FeedbackSchema()
        data = schema.load(request.json)
        
        # Store feedback for model improvement
        feedback_data = {
            'user_id': str(current_user.id),
            'prediction_id': data['prediction_id'],
            'rating': data['rating'],
            'comment': data.get('comment', ''),
            'is_helpful': data['is_helpful'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log feedback
        audit_log = AuditLog(
            user_id=current_user.id,
            action='feedback_submitted',
            resource_type='prediction',
            resource_id=data['prediction_id'],
            details=str(feedback_data),
            status='success'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Feedback submitted successfully',
            'feedback_id': audit_log.id
        })
        
    except ValidationError as e:
        return jsonify({
            'error': 'Invalid input',
            'message': str(e.messages)
        }), 400
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Could not submit feedback'
        }), 500

# Model Performance Metrics
@api_bp.route('/model-metrics', methods=['GET'])
@require_api_key
def get_model_metrics():
    """Get model performance metrics (admin only)."""
    try:
        if not symptom_checker:
            return jsonify({
                'error': 'Models not initialized',
                'message': 'ML models are not loaded'
            }), 503
        
        metrics = symptom_checker.performance_metrics
        
        return jsonify({
            'metrics': metrics,
            'models_loaded': list(symptom_checker.models.keys()),
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting model metrics: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Could not retrieve metrics'
        }), 500

# Helper Functions
def get_or_create_session(session_id: Optional[str] = None) -> ChatSession:
    """Get existing session or create new one."""
    if session_id:
        session = ChatSession.query.filter_by(
            id=session_id, 
            user_id=current_user.id
        ).first()
        if session:
            return session
    
    # Create new session
    session = ChatSession(
        user_id=current_user.id,
        title=f"Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        status='active'
    )
    db.session.add(session)
    db.session.flush()  # Get ID without committing
    
    return session

def generate_assistant_response(
    analysis: SymptomAnalysis,
    predictions: List[PredictionResult],
    sentiment: Dict[str, Any]
) -> str:
    """Generate appropriate assistant response."""
    
    # Emergency response
    if analysis.emergency_flag:
        return (
            "⚠️ URGENT: Based on your symptoms, you may need immediate medical attention. "
            "Please contact emergency services (911) or go to the nearest emergency room. "
            "Do not delay seeking medical care."
        )
    
    # High severity response
    if analysis.severity_level in ['High', 'Critical']:
        response = (
            f"Your symptoms suggest a {analysis.severity_level.lower()} condition. "
            "I strongly recommend contacting your healthcare provider soon. "
        )
    else:
        response = (
            f"Based on your symptoms, I've identified a {analysis.severity_level.lower()} "
            "severity condition. "
        )
    
    # Add predictions
    if predictions:
        response += f"\nMost likely conditions:\n"
        for i, pred in enumerate(predictions[:3], 1):
            response += f"{i}. {pred.disease.replace('_', ' ').title()} "
            response += f"({pred.confidence} confidence)\n"
        
        # Add recommendations
        if predictions[0].recommendations:
            response += f"\nRecommendations:\n"
            for rec in predictions[0].recommendations[:3]:
                response += f"• {rec}\n"
    
    # Add emotional support if needed
    if sentiment.get('emotions', {}).get('anxiety', 0) > 0.3:
        response += (
            "\nI understand this can be concerning. Remember that early "
            "identification helps with better outcomes."
        )
    
    # Disclaimer
    response += (
        "\n\n⚠️ Important: This is an AI assessment and should not replace "
        "professional medical advice. Please consult with a healthcare provider "
        "for proper diagnosis and treatment."
    )
    
    return response

def create_health_report(
    session: ChatSession,
    report_type: str,
    include_recommendations: bool
) -> HealthReport:
    """Create a comprehensive health report."""
    
    # Generate report content based on session data
    symptoms = session.get_symptoms()
    conditions = session.get_conditions()
    
    # Get latest predictions from session messages
    latest_message = session.messages.filter_by(message_type='assistant').order_by(
        ChatMessage.created_at.desc()
    ).first()
    
    predictions = []
    if latest_message:
        predictions = latest_message.get_predictions()
    
    # Generate recommendations
    recommendations = []
    if include_recommendations and predictions:
        # This would use the ML model to generate personalized recommendations
        recommendations = [
            "Continue monitoring symptoms",
            "Stay hydrated and get adequate rest",
            "Follow up with healthcare provider if symptoms persist"
        ]
    
    report = HealthReport(
        user_id=current_user.id,
        session_id=session.id,
        title=f"Health Assessment - {datetime.utcnow().strftime('%Y-%m-%d')}",
        summary=f"Assessment based on {len(symptoms)} reported symptoms",
        report_type=f"session_{report_type}",
        severity_level=session.severity_level,
        emergency_flag=session.emergency_flag,
        generated_by="AI Assistant v1.0"
    )
    
    report.symptoms = str(symptoms)
    report.predictions = str(predictions)
    report.recommendations = str(recommendations)
    
    db.session.add(report)
    db.session.commit()
    
    return report
