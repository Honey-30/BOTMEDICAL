"""
Advanced AI Healthcare Chatbot for Symptom Checking
Flask Web Application with Enhanced Security, ML Models, and User Management

This application provides comprehensive healthcare symptom analysis with:
- Advanced ML models for accurate predictions
- Secure user authentication and data protection
- Real-time chat interface with NLP processing
- Comprehensive health reporting
- API for third-party integrations
"""

import os
import logging
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user
from flask_mail import Mail
from flask_caching import Cache
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from prometheus_flask_exporter import PrometheusMetrics
import structlog
from datetime import datetime, timedelta
import json

# Import configuration and models
from config import config
from app.models import db, User, ChatSession, ChatMessage, HealthReport, AuditLog
from app.api.routes import api_bp, init_ml_models
from app.utils.security import security_manager, apply_security_headers
from app.utils.cache import cache_manager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def create_app(config_name='development'):
    """Application factory pattern for creating Flask app."""
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize Sentry for error tracking
    if app.config.get('SENTRY_DSN'):
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[
                FlaskIntegration(transaction_style='endpoint'),
                SqlalchemyIntegration()
            ],
            traces_sample_rate=0.1,
            environment=config_name
        )
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Initialize caching
    cache = Cache(app)
    cache_manager.config = app.config
    
    # Initialize CORS
    CORS(app, origins=['http://localhost:3000', 'https://yourdomain.com'])
    
    # Initialize rate limiting
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://'),
        default_limits=[app.config.get('RATELIMIT_DEFAULT', '100 per hour')]
    )
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Initialize email
    mail = Mail(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # Initialize Prometheus metrics
    if config_name == 'production':
        metrics = PrometheusMetrics(app)
        metrics.info('app_info', 'Healthcare Chatbot Application')
    
    # Initialize ML models
    init_ml_models(app.config)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Create authentication blueprint
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)
    
    # Create admin blueprint
    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error("Internal server error", exc_info=True)
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    # Before request handlers
    @app.before_request
    def before_request():
        """Execute before each request."""
        g.start_time = datetime.utcnow()
        
        # Security checks
        if request.endpoint and request.endpoint.startswith('admin.'):
            if not current_user.is_authenticated or not current_user.is_admin:
                return redirect(url_for('auth.login'))
    
    # After request handlers
    @app.after_request
    def after_request(response):
        """Execute after each request."""
        # Apply security headers
        response = apply_security_headers(response)
        
        # Log request
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            logger.info(
                "Request completed",
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                duration=duration,
                user_id=str(current_user.id) if current_user.is_authenticated else None
            )
        
        return response
    
    # Main application routes
    @app.route('/')
    def index():
        """Main chat interface."""
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        return render_template('chat/index.html', user=current_user)
    
    @app.route('/about')
    def about():
        """About page with project information."""
        return render_template('about.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """User dashboard with health history."""
        # Get user's recent sessions
        recent_sessions = ChatSession.query.filter_by(
            user_id=current_user.id
        ).order_by(ChatSession.created_at.desc()).limit(5).all()
        
        # Get user's recent reports
        recent_reports = HealthReport.query.filter_by(
            user_id=current_user.id
        ).order_by(HealthReport.created_at.desc()).limit(3).all()
        
        return render_template(
            'dashboard.html',
            recent_sessions=recent_sessions,
            recent_reports=recent_reports
        )
    
    @app.route('/health-reports')
    @login_required
    def health_reports():
        """User's health reports."""
        reports = HealthReport.query.filter_by(
            user_id=current_user.id
        ).order_by(HealthReport.created_at.desc()).all()
        
        return render_template('health_reports.html', reports=reports)
    
    @app.route('/profile')
    @login_required
    def profile():
        """User profile management."""
        return render_template('profile.html', user=current_user)
    
    @app.route('/chat/<session_id>')
    @login_required
    def chat_session(session_id):
        """View specific chat session."""
        session = ChatSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first_or_404()
        
        messages = ChatMessage.query.filter_by(
            session_id=session.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return render_template(
            'chat/session.html',
            session=session,
            messages=messages
        )
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Application health check."""
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            
            # Check cache connection
            cache_status = cache_manager.redis_client is not None
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'connected',
                'cache': 'connected' if cache_status else 'local_only',
                'version': '2.0.0'
            })
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 503
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        admin_user = User.query.filter_by(email='admin@healthchatbot.com').first()
        if not admin_user:
            admin_user = User(
                email='admin@healthchatbot.com',
                username='admin',
                password='admin123',  # Change this in production!
                first_name='System',
                last_name='Administrator',
                is_active=True,
                is_verified=True
            )
            admin_user.is_admin = True
            db.session.add(admin_user)
            db.session.commit()
            logger.info("Default admin user created")
    
    logger.info("Application created successfully", config=config_name)
    return app

# Create directories if they don't exist
os.makedirs('models', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

@app.route('/')
def index():
    """Render the main chat interface."""
    # Generate a session ID if not already present
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['symptoms'] = []
    
    return render_template('index.html')

@app.route('/about')
def about():
    """Render the about page with project information."""
    return render_template('about.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Process chat messages from the user and return appropriate responses.
    
    Request body should contain a JSON with a 'message' field.
    """
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({
            'response': "I didn't catch that. Could you please describe your symptoms?",
            'symptoms': [],
            'predictions': []
        })
    
    # Extract symptoms from the user message
    extracted_symptoms = preprocessor.extract_symptoms(user_message)
    
    # Update session symptoms
    current_symptoms = session.get('symptoms', [])
    current_symptoms.extend([s for s in extracted_symptoms if s not in current_symptoms])
    session['symptoms'] = current_symptoms
    
    # If we have symptoms, make predictions
    if current_symptoms:
        # Check if it might be an emergency
        is_emergency = symptom_checker.is_emergency(current_symptoms)
        
        # Calculate severity
        severity_score, severity_level = symptom_checker.calculate_severity(current_symptoms)
        
        # Get predictions
        predictions = symptom_checker.predict(current_symptoms)
        
        # Get remedies for the top predictions
        remedies = {}
        for disease, _ in predictions[:3]:  # Top 3 predictions
            remedies[disease] = symptom_checker.get_remedies(disease)
        
        # Generate response
        response = response_generator.generate_prediction_response(
            predictions, current_symptoms, is_emergency, (severity_score, severity_level), remedies
        )
        
        # Generate follow-up questions if not an emergency
        followup_questions = []
        if not is_emergency and predictions:
            followup_questions = response_generator.generate_followup_questions(
                predictions[0][0], current_symptoms
            )
        
        # Format predictions for the frontend
        formatted_predictions = []
        for disease, probability in predictions:
            formatted_predictions.append({
                'disease': disease,
                'probability': float(probability),
                'info': symptom_checker.get_disease_info(disease),
                'remedies': symptom_checker.get_remedies(disease),
                'precautions': symptom_checker.get_precautions(disease)
            })
            
        return jsonify({
            'response': response,
            'symptoms': current_symptoms,
            'predictions': formatted_predictions,
            'emergency': is_emergency,
            'severity': {
                'score': float(severity_score),
                'level': severity_level
            },
            'followup_questions': followup_questions,
            'remedies': remedies
        })
    else:
        # No symptoms detected
        return jsonify({
            'response': "I couldn't identify any specific symptoms from what you've described. Could you please be more specific about how you're feeling?",
            'symptoms': [],
            'predictions': []
        })

@app.route('/api/reset', methods=['POST'])
def reset_session():
    """Reset the current session (clear symptoms)."""
    session['symptoms'] = []
    
    return jsonify({
        'response': "I've reset your symptom history. How can I help you today?",
        'symptoms': []
    })

@app.route('/api/symptoms', methods=['GET'])
def get_symptoms():
    """Return a list of all standard symptoms for autocomplete."""
    symptoms = preprocessor.get_all_standard_symptoms()
    return jsonify({
        'symptoms': symptoms
    })

@app.route('/api/initialize', methods=['GET'])
def initialize_data():
    """Initialize the system by downloading necessary data and training the model."""
    try:
        # Check if we need to download data
        data_path = os.path.join('data', 'disease_symptom_dataset.csv')
        
        if not os.path.exists(data_path):
            # Create sample data if it doesn't exist
            _create_sample_data()
            
        # Check if we need to train the model
        model_path = os.path.join('models', 'symptom_model.pkl')
        if not os.path.exists(model_path):
            # Import here to avoid circular imports
            from model.training import train_model
            train_model()
            
        # Load the model
        symptom_checker.load_model(os.path.join('models', 'symptom_model.pkl'))
            
        return jsonify({
            'success': True,
            'message': 'System initialized successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error initializing system: {str(e)}'
        }), 500

def _create_sample_data():
    """Create sample datasets for the application."""
    # Create disease-symptom dataset
    diseases = [
        "Common Cold", "Influenza", "Migraine", "Hypertension", "Diabetes",
        "Asthma", "Gastroenteritis", "Urinary Tract Infection", "Pneumonia", "Anemia",
        "Allergic Rhinitis", "Bronchitis", "Conjunctivitis", "Sinusitis", "Dermatitis",
        "Anxiety Disorder", "Depression", "Insomnia", "Hypothyroidism", "Hyperthyroidism"
    ]
    
    # Map common symptoms to each disease
    disease_symptoms = {
        "Common Cold": ["runny nose", "sneezing", "cough", "sore throat", "mild fever", "congestion"],
        "Influenza": ["high fever", "body ache", "chills", "fatigue", "cough", "headache"],
        "Migraine": ["severe headache", "nausea", "light sensitivity", "vision problems", "dizziness"],
        "Hypertension": ["headache", "chest pain", "shortness of breath", "dizziness", "fatigue"],
        "Diabetes": ["increased thirst", "frequent urination", "hunger", "fatigue", "weight loss"],
        "Asthma": ["wheezing", "shortness of breath", "chest tightness", "cough", "breathing difficulty"],
        "Gastroenteritis": ["diarrhoea", "vomiting", "abdominal pain", "nausea", "fever"],
        "Urinary Tract Infection": ["burning urination", "frequent urination", "abdominal pain", "cloudy urine"],
        "Pneumonia": ["cough", "high fever", "chest pain", "breathing difficulty", "fatigue"],
        "Anemia": ["fatigue", "weakness", "pale skin", "shortness of breath", "dizziness"],
        "Allergic Rhinitis": ["sneezing", "itchy eyes", "runny nose", "congestion", "watery eyes"],
        "Bronchitis": ["persistent cough", "mucus production", "fatigue", "mild fever", "chest discomfort"],
        "Conjunctivitis": ["red eyes", "itchy eyes", "watery eyes", "eye discharge", "sensitivity to light"],
        "Sinusitis": ["facial pressure", "nasal congestion", "thick nasal discharge", "reduced smell", "cough"],
        "Dermatitis": ["skin rash", "itchy skin", "red skin", "swelling", "dry skin"],
        "Anxiety Disorder": ["excessive worry", "restlessness", "fatigue", "difficulty concentrating", "irritability"],
        "Depression": ["persistent sadness", "loss of interest", "fatigue", "sleep problems", "appetite changes"],
        "Insomnia": ["difficulty falling asleep", "waking up at night", "daytime fatigue", "irritability"],
        "Hypothyroidism": ["fatigue", "weight gain", "cold sensitivity", "constipation", "dry skin"],
        "Hyperthyroidism": ["weight loss", "rapid heartbeat", "increased appetite", "anxiety", "tremors"]
    }
    
    # Create remedies dataset
    disease_remedies = {
        "Common Cold": [
            "Get plenty of rest", 
            "Stay hydrated with warm fluids", 
            "Use a humidifier", 
            "Take over-the-counter pain relievers"
        ],
        "Influenza": [
            "Rest and stay home", 
            "Drink plenty of fluids", 
            "Take acetaminophen or ibuprofen for fever", 
            "Consider antiviral medications if prescribed"
        ],
        "Migraine": [
            "Rest in a quiet, dark room", 
            "Apply cold or warm compresses", 
            "Practice relaxation techniques", 
            "Take prescribed migraine medications"
        ],
        "Hypertension": [
            "Reduce sodium intake", 
            "Regular physical activity", 
            "Limit alcohol consumption", 
            "Take prescribed medications regularly"
        ],
        "Diabetes": [
            "Follow a balanced diet plan", 
            "Regular physical activity", 
            "Monitor blood sugar levels", 
            "Take medications as prescribed"
        ],
        "Asthma": [
            "Avoid triggers", 
            "Use prescribed inhalers as directed", 
            "Follow an asthma action plan", 
            "Regular check-ups with healthcare provider"
        ],
        "Gastroenteritis": [
            "Stay hydrated with clear fluids", 
            "Gradual return to normal diet", 
            "Rest", 
            "Over-the-counter rehydration solutions"
        ],
        "Urinary Tract Infection": [
            "Drink plenty of water", 
            "Take prescribed antibiotics", 
            "Use a heating pad", 
            "Avoid caffeine and alcohol"
        ],
        "Pneumonia": [
            "Get plenty of rest", 
            "Take prescribed antibiotics", 
            "Stay hydrated", 
            "Use prescribed pain relievers"
        ],
        "Anemia": [
            "Iron-rich diet", 
            "Vitamin C to increase iron absorption", 
            "Prescribed iron supplements", 
            "Treat underlying causes"
        ],
    }
    
    # Add remedies for the remaining diseases
    for disease in diseases:
        if disease not in disease_remedies:
            disease_remedies[disease] = [
                "Consult with a healthcare professional",
                "Follow prescribed treatment plan",
                "Maintain a healthy lifestyle",
                "Regular check-ups"
            ]
    
    # Create DataFrame for disease-symptom dataset
    max_symptoms = max(len(symptoms) for symptoms in disease_symptoms.values())
    symptom_cols = [f"Symptom_{i+1}" for i in range(max_symptoms)]
    
    data = []
    for disease in diseases:
        symptoms = disease_symptoms[disease]
        # Pad with empty strings if needed
        symptoms_padded = symptoms + [''] * (max_symptoms - len(symptoms))
        data.append([disease] + symptoms_padded)
    
    df = pd.DataFrame(data, columns=['Disease'] + symptom_cols)
    df.to_csv(os.path.join('data', 'disease_symptom_dataset.csv'), index=False)
    
    # Create severity data
    all_symptoms = set()
    for symptoms in disease_symptoms.values():
        all_symptoms.update(symptoms)
    
    import random
    severity_data = [[symptom, random.randint(1, 10)] for symptom in all_symptoms]
    severity_df = pd.DataFrame(severity_data, columns=['Symptom', 'weight'])
    severity_df.to_csv(os.path.join('data', 'symptom_severity.csv'), index=False)
    
    # Create remedies dataset
    remedies_data = []
    for disease, remedies in disease_remedies.items():
        for remedy in remedies:
            remedies_data.append([disease, remedy])
    
    remedies_df = pd.DataFrame(remedies_data, columns=['Disease', 'Remedy'])
    remedies_df.to_csv(os.path.join('data', 'remedies_dataset.csv'), index=False)
    
    print(f"Created sample datasets with {len(diseases)} diseases and {len(all_symptoms)} symptoms")

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)