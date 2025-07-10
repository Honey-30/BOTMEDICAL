"""
Admin routes for the healthcare chatbot.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import logging

from ..models import db, User, ChatSession, ChatMessage, HealthReport, AuditLog
from ..utils.security import require_permission
from ..utils.cache import get_cache_info, clear_all_cache

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def require_admin():
    """Ensure user is admin for all admin routes."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard."""
    try:
        # Get statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_sessions = ChatSession.query.count()
        total_messages = ChatMessage.query.count()
        total_reports = HealthReport.query.count()
        
        # Recent activity
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_sessions = ChatSession.query.order_by(ChatSession.created_at.desc()).limit(5).all()
        
        # Usage statistics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_sessions_count = ChatSession.query.filter(
            ChatSession.created_at >= thirty_days_ago
        ).count()
        
        recent_messages_count = ChatMessage.query.filter(
            ChatMessage.created_at >= thirty_days_ago
        ).count()
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'total_reports': total_reports,
            'recent_sessions_30d': recent_sessions_count,
            'recent_messages_30d': recent_messages_count,
            'avg_messages_per_session': total_messages / total_sessions if total_sessions > 0 else 0
        }
        
        return render_template(
            'admin/dashboard.html',
            stats=stats,
            recent_users=recent_users,
            recent_sessions=recent_sessions
        )
        
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        flash('Error loading dashboard data.', 'error')
        return render_template('admin/dashboard.html', stats={}, recent_users=[], recent_sessions=[])

@admin_bp.route('/users')
@login_required
def users():
    """User management."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get search and filter parameters
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'all')
    
    # Build query
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.email.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
        )
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    elif status_filter == 'verified':
        query = query.filter_by(is_verified=True)
    elif status_filter == 'unverified':
        query = query.filter_by(is_verified=False)
    
    # Order by creation date (newest first)
    query = query.order_by(User.created_at.desc())
    
    # Paginate
    users_pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template(
        'admin/users.html',
        users=users_pagination.items,
        pagination=users_pagination,
        search=search,
        status_filter=status_filter
    )

@admin_bp.route('/users/<user_id>')
@login_required
def user_detail(user_id):
    """User detail view."""
    user = User.query.get_or_404(user_id)
    
    # Get user's sessions
    sessions = ChatSession.query.filter_by(user_id=user.id).order_by(
        ChatSession.created_at.desc()
    ).limit(10).all()
    
    # Get user's reports
    reports = HealthReport.query.filter_by(user_id=user.id).order_by(
        HealthReport.created_at.desc()
    ).limit(5).all()
    
    # Get recent audit logs for this user
    audit_logs = AuditLog.query.filter_by(user_id=user.id).order_by(
        AuditLog.created_at.desc()
    ).limit(10).all()
    
    return render_template(
        'admin/user_detail.html',
        user=user,
        sessions=sessions,
        reports=reports,
        audit_logs=audit_logs
    )

@admin_bp.route('/users/<user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Toggle user active status."""
    try:
        user = User.query.get_or_404(user_id)
        
        # Don't allow disabling the current admin user
        if user.id == current_user.id:
            return jsonify({
                'error': 'Cannot disable your own account'
            }), 400
        
        user.is_active = not user.is_active
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log the action
        audit_log = AuditLog(
            user_id=current_user.id,
            action='user_status_changed',
            resource_type='user',
            resource_id=str(user.id),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            endpoint=request.endpoint,
            status='success',
            details=f"User {user.email} status changed to {'active' if user.is_active else 'inactive'}"
        )
        db.session.add(audit_log)
        db.session.commit()
        
        logger.info(f"Admin {current_user.email} changed user {user.email} status to {'active' if user.is_active else 'inactive'}")
        
        return jsonify({
            'message': f"User {'activated' if user.is_active else 'deactivated'} successfully",
            'new_status': 'active' if user.is_active else 'inactive'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling user status: {str(e)}")
        return jsonify({
            'error': 'Failed to update user status'
        }), 500

@admin_bp.route('/sessions')
@login_required
def sessions():
    """Chat sessions management."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    emergency_only = request.args.get('emergency') == 'true'
    severity_filter = request.args.get('severity', 'all')
    
    # Build query
    query = ChatSession.query
    
    if emergency_only:
        query = query.filter_by(emergency_flag=True)
    
    if severity_filter != 'all':
        query = query.filter_by(severity_level=severity_filter)
    
    # Order by creation date (newest first)
    query = query.order_by(ChatSession.created_at.desc())
    
    # Paginate
    sessions_pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template(
        'admin/sessions.html',
        sessions=sessions_pagination.items,
        pagination=sessions_pagination,
        emergency_only=emergency_only,
        severity_filter=severity_filter
    )

@admin_bp.route('/sessions/<session_id>')
@login_required
def session_detail(session_id):
    """Chat session detail view."""
    session = ChatSession.query.get_or_404(session_id)
    
    # Get session messages
    messages = ChatMessage.query.filter_by(session_id=session.id).order_by(
        ChatMessage.created_at.asc()
    ).all()
    
    return render_template(
        'admin/session_detail.html',
        session=session,
        messages=messages
    )

@admin_bp.route('/reports')
@login_required
def reports():
    """Health reports management."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    report_type = request.args.get('type', 'all')
    emergency_only = request.args.get('emergency') == 'true'
    
    # Build query
    query = HealthReport.query
    
    if report_type != 'all':
        query = query.filter_by(report_type=report_type)
    
    if emergency_only:
        query = query.filter_by(emergency_flag=True)
    
    # Order by creation date (newest first)
    query = query.order_by(HealthReport.created_at.desc())
    
    # Paginate
    reports_pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template(
        'admin/reports.html',
        reports=reports_pagination.items,
        pagination=reports_pagination,
        report_type=report_type,
        emergency_only=emergency_only
    )

@admin_bp.route('/audit-logs')
@login_required
def audit_logs():
    """Audit logs management."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Get filter parameters
    action_filter = request.args.get('action', 'all')
    status_filter = request.args.get('status', 'all')
    user_filter = request.args.get('user_id', '')
    
    # Build query
    query = AuditLog.query
    
    if action_filter != 'all':
        query = query.filter_by(action=action_filter)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if user_filter:
        query = query.filter_by(user_id=user_filter)
    
    # Order by creation date (newest first)
    query = query.order_by(AuditLog.created_at.desc())
    
    # Paginate
    logs_pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Get unique actions and users for filters
    unique_actions = db.session.query(AuditLog.action).distinct().all()
    unique_actions = [action[0] for action in unique_actions if action[0]]
    
    return render_template(
        'admin/audit_logs.html',
        logs=logs_pagination.items,
        pagination=logs_pagination,
        action_filter=action_filter,
        status_filter=status_filter,
        user_filter=user_filter,
        unique_actions=unique_actions
    )

@admin_bp.route('/system-info')
@login_required
def system_info():
    """System information and diagnostics."""
    try:
        # Get cache information
        cache_info = get_cache_info()
        
        # Get database statistics
        db_stats = {
            'users': User.query.count(),
            'sessions': ChatSession.query.count(),
            'messages': ChatMessage.query.count(),
            'reports': HealthReport.query.count(),
            'audit_logs': AuditLog.query.count()
        }
        
        # Get recent errors from audit logs
        recent_errors = AuditLog.query.filter_by(status='error').order_by(
            AuditLog.created_at.desc()
        ).limit(10).all()
        
        return render_template(
            'admin/system_info.html',
            cache_info=cache_info,
            db_stats=db_stats,
            recent_errors=recent_errors
        )
        
    except Exception as e:
        logger.error(f"Error loading system info: {str(e)}")
        flash('Error loading system information.', 'error')
        return render_template('admin/system_info.html', cache_info={}, db_stats={}, recent_errors=[])

@admin_bp.route('/clear-cache', methods=['POST'])
@login_required
def clear_cache():
    """Clear application cache."""
    try:
        success = clear_all_cache()
        
        # Log the action
        audit_log = AuditLog(
            user_id=current_user.id,
            action='cache_cleared',
            resource_type='system',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            endpoint=request.endpoint,
            status='success' if success else 'failed'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        if success:
            logger.info(f"Admin {current_user.email} cleared application cache")
            return jsonify({'message': 'Cache cleared successfully'})
        else:
            return jsonify({'error': 'Failed to clear cache'}), 500
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({'error': 'Failed to clear cache'}), 500

@admin_bp.route('/export-data')
@login_required
def export_data():
    """Export system data (placeholder for future implementation)."""
    # This would implement data export functionality
    # For now, just return a placeholder response
    return jsonify({
        'message': 'Data export functionality not yet implemented',
        'note': 'This feature would allow exporting user data, sessions, and reports'
    })

@admin_bp.route('/analytics')
@login_required
def analytics():
    """System analytics and insights."""
    try:
        # Calculate various metrics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        
        # Usage trends (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_sessions = []
        daily_messages = []
        
        for i in range(7):
            day = seven_days_ago + timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            session_count = ChatSession.query.filter(
                ChatSession.created_at >= day_start,
                ChatSession.created_at < day_end
            ).count()
            
            message_count = ChatMessage.query.filter(
                ChatMessage.created_at >= day_start,
                ChatMessage.created_at < day_end
            ).count()
            
            daily_sessions.append({
                'date': day.strftime('%Y-%m-%d'),
                'count': session_count
            })
            
            daily_messages.append({
                'date': day.strftime('%Y-%m-%d'),
                'count': message_count
            })
        
        # Emergency cases
        emergency_sessions = ChatSession.query.filter_by(emergency_flag=True).count()
        emergency_rate = (emergency_sessions / ChatSession.query.count() * 100) if ChatSession.query.count() > 0 else 0
        
        # Top symptoms (this would require proper symptom tracking)
        # For now, just return placeholder data
        top_symptoms = [
            {'symptom': 'Headache', 'count': 45},
            {'symptom': 'Fever', 'count': 38},
            {'symptom': 'Cough', 'count': 32},
            {'symptom': 'Fatigue', 'count': 28},
            {'symptom': 'Nausea', 'count': 22}
        ]
        
        analytics_data = {
            'total_users': total_users,
            'active_users': active_users,
            'user_growth_rate': 0,  # Placeholder
            'daily_sessions': daily_sessions,
            'daily_messages': daily_messages,
            'emergency_sessions': emergency_sessions,
            'emergency_rate': round(emergency_rate, 2),
            'top_symptoms': top_symptoms,
            'avg_session_length': 0,  # Placeholder
            'user_satisfaction': 0  # Placeholder
        }
        
        return render_template('admin/analytics.html', analytics=analytics_data)
        
    except Exception as e:
        logger.error(f"Error loading analytics: {str(e)}")
        flash('Error loading analytics data.', 'error')
        return render_template('admin/analytics.html', analytics={})
