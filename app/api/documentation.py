"""
OpenAPI/Swagger documentation configuration for the AI Healthcare Chatbot API.
"""

from flask import Blueprint, jsonify, render_template_string
from flask_restx import Api, Resource, fields, Namespace
from flask_login import login_required
import json

# Create API blueprint
api_bp = Blueprint('api_docs', __name__, url_prefix='/api-docs')

# Initialize Flask-RESTX
api = Api(
    api_bp,
    version='1.0',
    title='AI Healthcare Chatbot API',
    description='Advanced AI-powered healthcare chatbot with comprehensive medical assistance capabilities',
    doc='/docs/',
    contact={
        'name': 'API Support',
        'email': 'support@healthchatbot.com',
        'url': 'https://healthchatbot.com/support'
    },
    license={
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/MIT'
    },
    terms_url='https://healthchatbot.com/terms',
    security='Bearer',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Bearer token for authentication'
        }
    }
)

# Define namespaces
chat_ns = Namespace('chat', description='Chat and conversation management')
health_ns = Namespace('health', description='Health analysis and monitoring')
auth_ns = Namespace('auth', description='Authentication and authorization')
admin_ns = Namespace('admin', description='Administrative operations')
system_ns = Namespace('system', description='System health and monitoring')

api.add_namespace(chat_ns)
api.add_namespace(health_ns)
api.add_namespace(auth_ns)
api.add_namespace(admin_ns)
api.add_namespace(system_ns)

# Common models
error_model = api.model('Error', {
    'success': fields.Boolean(default=False),
    'error': fields.String(required=True, description='Error message'),
    'code': fields.String(description='Error code'),
    'timestamp': fields.DateTime(description='Error timestamp')
})

user_model = api.model('User', {
    'id': fields.String(required=True, description='User ID'),
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email address'),
    'full_name': fields.String(description='Full name'),
    'age': fields.Integer(description='Age'),
    'gender': fields.String(description='Gender'),
    'created_at': fields.DateTime(description='Account creation date'),
    'is_active': fields.Boolean(description='Account status'),
    'health_score': fields.Integer(description='Overall health score')
})

# Chat models
chat_message_model = api.model('ChatMessage', {
    'id': fields.String(required=True, description='Message ID'),
    'sender': fields.String(required=True, description='Message sender (user/bot)', enum=['user', 'bot']),
    'content': fields.String(required=True, description='Message content'),
    'timestamp': fields.DateTime(required=True, description='Message timestamp'),
    'metadata': fields.Raw(description='Additional message metadata')
})

chat_session_model = api.model('ChatSession', {
    'id': fields.String(required=True, description='Session ID'),
    'user_id': fields.String(required=True, description='User ID'),
    'title': fields.String(description='Session title'),
    'created_at': fields.DateTime(required=True, description='Session creation time'),
    'updated_at': fields.DateTime(description='Last update time'),
    'is_active': fields.Boolean(description='Session status'),
    'message_count': fields.Integer(description='Number of messages'),
    'messages': fields.List(fields.Nested(chat_message_model), description='Session messages')
})

chat_request_model = api.model('ChatRequest', {
    'message': fields.String(required=True, description='User message', min_length=1, max_length=1000),
    'session_id': fields.String(description='Existing session ID (optional)'),
    'context': fields.Raw(description='Additional context data')
})

chat_response_model = api.model('ChatResponse', {
    'success': fields.Boolean(required=True, description='Request success status'),
    'response': fields.String(required=True, description='Bot response'),
    'session_id': fields.String(required=True, description='Session ID'),
    'message_id': fields.String(required=True, description='Message ID'),
    'emergency_detected': fields.Boolean(description='Emergency situation detected'),
    'confidence': fields.Float(description='Response confidence score'),
    'suggestions': fields.List(fields.String, description='Quick suggestion prompts'),
    'metadata': fields.Raw(description='Additional response metadata')
})

# Health models
symptom_model = api.model('Symptom', {
    'name': fields.String(required=True, description='Symptom name'),
    'severity': fields.Integer(description='Severity level (1-10)'),
    'duration': fields.String(description='Duration of symptom'),
    'description': fields.String(description='Additional symptom description')
})

symptom_analysis_request_model = api.model('SymptomAnalysisRequest', {
    'symptoms': fields.List(fields.String, required=True, description='List of symptoms'),
    'demographics': fields.Raw(description='User demographic information'),
    'medical_history': fields.Raw(description='Medical history information')
})

symptom_analysis_response_model = api.model('SymptomAnalysisResponse', {
    'success': fields.Boolean(required=True, description='Analysis success status'),
    'analysis': fields.Raw(required=True, description='Symptom analysis results'),
    'risk_level': fields.String(required=True, description='Risk assessment', enum=['low', 'medium', 'high', 'emergency']),
    'confidence': fields.Float(required=True, description='Analysis confidence score'),
    'recommendations': fields.List(fields.String, description='Health recommendations'),
    'emergency_alert': fields.Boolean(description='Emergency situation detected'),
    'suggested_actions': fields.List(fields.String, description='Suggested next steps'),
    'specialist_referral': fields.String(description='Recommended specialist type')
})

health_report_model = api.model('HealthReport', {
    'id': fields.String(required=True, description='Report ID'),
    'user_id': fields.String(required=True, description='User ID'),
    'report_type': fields.String(required=True, description='Report type'),
    'health_score': fields.Integer(required=True, description='Overall health score'),
    'generated_at': fields.DateTime(required=True, description='Report generation time'),
    'summary': fields.String(description='Executive summary'),
    'recommendations': fields.List(fields.String, description='Health recommendations'),
    'risk_factors': fields.List(fields.String, description='Identified risk factors'),
    'improvements': fields.List(fields.String, description='Health improvements'),
    'concerns': fields.List(fields.String, description='Health concerns'),
    'next_steps': fields.List(fields.String, description='Recommended next steps')
})

# Authentication models
login_request_model = api.model('LoginRequest', {
    'username': fields.String(required=True, description='Username or email'),
    'password': fields.String(required=True, description='Password')
})

login_response_model = api.model('LoginResponse', {
    'success': fields.Boolean(required=True, description='Login success status'),
    'access_token': fields.String(description='JWT access token'),
    'refresh_token': fields.String(description='JWT refresh token'),
    'user': fields.Nested(user_model, description='User information'),
    'expires_in': fields.Integer(description='Token expiration time in seconds')
})

register_request_model = api.model('RegisterRequest', {
    'username': fields.String(required=True, description='Desired username', min_length=3, max_length=20),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(required=True, description='Password', min_length=8),
    'full_name': fields.String(required=True, description='Full name'),
    'age': fields.Integer(required=True, description='Age', min=13, max=120),
    'gender': fields.String(description='Gender', enum=['male', 'female', 'other', 'prefer_not_to_say'])
})

# System models
health_check_model = api.model('HealthCheck', {
    'status': fields.String(required=True, description='System health status', enum=['healthy', 'degraded', 'unhealthy']),
    'timestamp': fields.DateTime(required=True, description='Check timestamp'),
    'version': fields.String(description='Application version'),
    'uptime': fields.String(description='System uptime'),
    'components': fields.Raw(description='Component health status'),
    'metrics': fields.Raw(description='System metrics')
})

feedback_request_model = api.model('FeedbackRequest', {
    'message_id': fields.String(required=True, description='Message ID to provide feedback for'),
    'feedback': fields.String(required=True, description='Feedback type', enum=['positive', 'negative']),
    'comment': fields.String(description='Optional feedback comment'),
    'rating': fields.Integer(description='Rating score (1-5)')
})

# Chat namespace endpoints
@chat_ns.route('/send')
class ChatSend(Resource):
    @api.doc('send_message')
    @api.expect(chat_request_model)
    @api.marshal_with(chat_response_model)
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized', error_model)
    @api.response(429, 'Rate Limit Exceeded', error_model)
    @login_required
    def post(self):
        """Send a message to the AI healthcare chatbot."""
        pass

@chat_ns.route('/sessions')
class ChatSessions(Resource):
    @api.doc('get_chat_sessions')
    @api.marshal_list_with(chat_session_model)
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized', error_model)
    @login_required
    def get(self):
        """Get user's chat sessions."""
        pass

@chat_ns.route('/sessions/<string:session_id>')
class ChatSessionDetail(Resource):
    @api.doc('get_chat_session')
    @api.marshal_with(chat_session_model)
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized', error_model)
    @api.response(404, 'Session Not Found', error_model)
    @login_required
    def get(self, session_id):
        """Get specific chat session details."""
        pass

    @api.doc('delete_chat_session')
    @api.response(200, 'Session deleted successfully')
    @api.response(401, 'Unauthorized', error_model)
    @api.response(404, 'Session Not Found', error_model)
    @login_required
    def delete(self, session_id):
        """Delete a chat session."""
        pass

@chat_ns.route('/feedback')
class ChatFeedback(Resource):
    @api.doc('submit_feedback')
    @api.expect(feedback_request_model)
    @api.response(200, 'Feedback submitted successfully')
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized', error_model)
    @login_required
    def post(self):
        """Submit feedback for a chat message."""
        pass

# Health namespace endpoints
@health_ns.route('/analyze-symptoms')
class SymptomAnalysis(Resource):
    @api.doc('analyze_symptoms')
    @api.expect(symptom_analysis_request_model)
    @api.marshal_with(symptom_analysis_response_model)
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized', error_model)
    @login_required
    def post(self):
        """Analyze symptoms and provide health assessment."""
        pass

@health_ns.route('/reports')
class HealthReports(Resource):
    @api.doc('get_health_reports')
    @api.marshal_list_with(health_report_model)
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized', error_model)
    @login_required
    def get(self):
        """Get user's health reports."""
        pass

@health_ns.route('/reports/generate')
class GenerateHealthReport(Resource):
    @api.doc('generate_health_report')
    @api.expect(api.model('GenerateReportRequest', {
        'session_id': fields.String(description='Chat session ID to base report on'),
        'report_type': fields.String(required=True, description='Report type', enum=['general', 'symptoms', 'comprehensive'])
    }))
    @api.marshal_with(health_report_model)
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized', error_model)
    @login_required
    def post(self):
        """Generate a health report."""
        pass

@health_ns.route('/reports/<string:report_id>')
class HealthReportDetail(Resource):
    @api.doc('get_health_report')
    @api.marshal_with(health_report_model)
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized', error_model)
    @api.response(404, 'Report Not Found', error_model)
    @login_required
    def get(self, report_id):
        """Get specific health report."""
        pass

@health_ns.route('/emergency')
class EmergencyCheck(Resource):
    @api.doc('emergency_check')
    @api.expect(api.model('EmergencyCheckRequest', {
        'text': fields.String(required=True, description='Text to analyze for emergency situations')
    }))
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized', error_model)
    @login_required
    def post(self):
        """Check if text indicates an emergency situation."""
        pass

# Authentication namespace endpoints
@auth_ns.route('/login')
class Login(Resource):
    @api.doc('user_login')
    @api.expect(login_request_model)
    @api.marshal_with(login_response_model)
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Invalid Credentials', error_model)
    def post(self):
        """Authenticate user and return access token."""
        pass

@auth_ns.route('/register')
class Register(Resource):
    @api.doc('user_register')
    @api.expect(register_request_model)
    @api.marshal_with(login_response_model)
    @api.response(201, 'User created successfully')
    @api.response(400, 'Bad Request', error_model)
    @api.response(409, 'User already exists', error_model)
    def post(self):
        """Register a new user account."""
        pass

@auth_ns.route('/refresh')
class RefreshToken(Resource):
    @api.doc('refresh_token')
    @api.expect(api.model('RefreshTokenRequest', {
        'refresh_token': fields.String(required=True, description='Refresh token')
    }))
    @api.response(200, 'Token refreshed successfully')
    @api.response(401, 'Invalid refresh token', error_model)
    def post(self):
        """Refresh access token using refresh token."""
        pass

@auth_ns.route('/logout')
class Logout(Resource):
    @api.doc('user_logout')
    @api.response(200, 'Logged out successfully')
    @api.response(401, 'Unauthorized', error_model)
    @login_required
    def post(self):
        """Logout user and invalidate tokens."""
        pass

# System namespace endpoints
@system_ns.route('/health')
class SystemHealth(Resource):
    @api.doc('system_health_check')
    @api.marshal_with(health_check_model)
    @api.response(200, 'System is healthy')
    @api.response(503, 'System is unhealthy', error_model)
    def get(self):
        """Check system health status."""
        pass

@system_ns.route('/metrics')
class SystemMetrics(Resource):
    @api.doc('system_metrics')
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized', error_model)
    @login_required
    def get(self):
        """Get system performance metrics."""
        pass

@system_ns.route('/version')
class SystemVersion(Resource):
    @api.doc('system_version')
    @api.response(200, 'Success')
    def get(self):
        """Get application version information."""
        pass

# Admin namespace endpoints (require admin privileges)
@admin_ns.route('/users')
class AdminUsers(Resource):
    @api.doc('admin_get_users')
    @api.marshal_list_with(user_model)
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized', error_model)
    @api.response(403, 'Forbidden', error_model)
    def get(self):
        """Get all users (admin only)."""
        pass

@admin_ns.route('/users/<string:user_id>')
class AdminUserDetail(Resource):
    @api.doc('admin_get_user')
    @api.marshal_with(user_model)
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized', error_model)
    @api.response(403, 'Forbidden', error_model)
    @api.response(404, 'User Not Found', error_model)
    def get(self, user_id):
        """Get specific user details (admin only)."""
        pass

    @api.doc('admin_delete_user')
    @api.response(200, 'User deleted successfully')
    @api.response(401, 'Unauthorized', error_model)
    @api.response(403, 'Forbidden', error_model)
    @api.response(404, 'User Not Found', error_model)
    def delete(self, user_id):
        """Delete user account (admin only)."""
        pass

@admin_ns.route('/sessions')
class AdminSessions(Resource):
    @api.doc('admin_get_sessions')
    @api.marshal_list_with(chat_session_model)
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized', error_model)
    @api.response(403, 'Forbidden', error_model)
    def get(self):
        """Get all chat sessions (admin only)."""
        pass

@admin_ns.route('/stats')
class AdminStats(Resource):
    @api.doc('admin_get_stats')
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized', error_model)
    @api.response(403, 'Forbidden', error_model)
    def get(self):
        """Get system statistics (admin only)."""
        pass

# API documentation routes
@api_bp.route('/openapi.json')
def openapi_spec():
    """Return OpenAPI specification as JSON."""
    return jsonify(api.__schema__)

@api_bp.route('/redoc')
def redoc():
    """Serve ReDoc documentation."""
    redoc_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Healthcare Chatbot API - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body { margin: 0; padding: 0; }
        </style>
    </head>
    <body>
        <redoc spec-url="/api-docs/openapi.json"></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return render_template_string(redoc_html)

@api_bp.route('/postman')
def postman_collection():
    """Export Postman collection."""
    # This would generate a Postman collection from the OpenAPI spec
    # For now, return a basic structure
    collection = {
        "info": {
            "name": "AI Healthcare Chatbot API",
            "description": "API collection for AI Healthcare Chatbot",
            "version": "1.0.0",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{access_token}}",
                    "type": "string"
                }
            ]
        },
        "variable": [
            {
                "key": "base_url",
                "value": "{{base_url}}",
                "type": "string"
            }
        ],
        "item": [
            {
                "name": "Authentication",
                "item": [
                    {
                        "name": "Login",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": "{\n  \"username\": \"{{username}}\",\n  \"password\": \"{{password}}\"\n}"
                            },
                            "url": {
                                "raw": "{{base_url}}/api/auth/login",
                                "host": ["{{base_url}}"],
                                "path": ["api", "auth", "login"]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Chat",
                "item": [
                    {
                        "name": "Send Message",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": "{\n  \"message\": \"I have a headache\"\n}"
                            },
                            "url": {
                                "raw": "{{base_url}}/api/chat/send",
                                "host": ["{{base_url}}"],
                                "path": ["api", "chat", "send"]
                            }
                        }
                    }
                ]
            }
        ]
    }
    
    return jsonify(collection)

# Error handlers
@api.errorhandler(400)
def bad_request(error):
    return {'success': False, 'error': 'Bad request', 'message': str(error)}, 400

@api.errorhandler(401)
def unauthorized(error):
    return {'success': False, 'error': 'Unauthorized', 'message': 'Authentication required'}, 401

@api.errorhandler(403)
def forbidden(error):
    return {'success': False, 'error': 'Forbidden', 'message': 'Insufficient permissions'}, 403

@api.errorhandler(404)
def not_found(error):
    return {'success': False, 'error': 'Not found', 'message': 'Resource not found'}, 404

@api.errorhandler(429)
def rate_limit_exceeded(error):
    return {'success': False, 'error': 'Rate limit exceeded', 'message': 'Too many requests'}, 429

@api.errorhandler(500)
def internal_error(error):
    return {'success': False, 'error': 'Internal server error', 'message': 'An unexpected error occurred'}, 500
