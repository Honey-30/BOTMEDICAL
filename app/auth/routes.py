"""
Authentication routes for the healthcare chatbot.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import logging
import re

from ..models import db, User, AuditLog
from ..utils.security import (
    security_manager, 
    validate_password_strength, 
    sanitize_input,
    rate_limiter
)
from ..utils.cache import invalidate_user_cache

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            # Rate limiting
            client_ip = request.remote_addr
            if not rate_limiter.is_allowed(f"login:{client_ip}", 5, 300):  # 5 attempts per 5 minutes
                logger.warning(f"Rate limit exceeded for login attempts from {client_ip}")
                return jsonify({
                    'error': 'Too many login attempts',
                    'message': 'Please try again in 5 minutes'
                }), 429
            
            # Get form data
            data = request.get_json() if request.is_json else request.form
            email = sanitize_input(data.get('email', '').strip().lower())
            password = data.get('password', '')
            remember_me = data.get('remember_me', False)
            
            # Validation
            if not email or not password:
                return jsonify({
                    'error': 'Missing credentials',
                    'message': 'Email and password are required'
                }), 400
            
            # Email format validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({
                    'error': 'Invalid email',
                    'message': 'Please enter a valid email address'
                }), 400
            
            # Find user
            user = User.query.filter_by(email=email).first()
            
            if not user or not user.check_password(password):
                # Log failed attempt
                audit_log = AuditLog(
                    action='login_failed',
                    resource_type='user',
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    endpoint=request.endpoint,
                    status='failed',
                    details=f"Failed login attempt for email: {email}"
                )
                db.session.add(audit_log)
                db.session.commit()
                
                logger.warning(f"Failed login attempt for email: {email}")
                return jsonify({
                    'error': 'Invalid credentials',
                    'message': 'Invalid email or password'
                }), 401
            
            # Check if user is active
            if not user.is_active:
                return jsonify({
                    'error': 'Account disabled',
                    'message': 'Your account has been disabled. Please contact support.'
                }), 403
            
            # Login user
            login_user(user, remember=remember_me)
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log successful login
            audit_log = AuditLog(
                user_id=user.id,
                action='login_success',
                resource_type='user',
                resource_id=str(user.id),
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                endpoint=request.endpoint,
                status='success'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            logger.info(f"User {user.email} logged in successfully")
            
            # Return response
            if request.is_json:
                return jsonify({
                    'message': 'Login successful',
                    'user': user.to_dict(),
                    'redirect_url': url_for('dashboard')
                })
            else:
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
                
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return jsonify({
                'error': 'Login failed',
                'message': 'An error occurred during login'
            }), 500
    
    # GET request - show login form
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration endpoint."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            # Rate limiting
            client_ip = request.remote_addr
            if not rate_limiter.is_allowed(f"register:{client_ip}", 3, 3600):  # 3 attempts per hour
                return jsonify({
                    'error': 'Too many registration attempts',
                    'message': 'Please try again in an hour'
                }), 429
            
            # Get form data
            data = request.get_json() if request.is_json else request.form
            email = sanitize_input(data.get('email', '').strip().lower())
            username = sanitize_input(data.get('username', '').strip())
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', '')
            first_name = sanitize_input(data.get('first_name', '').strip())
            last_name = sanitize_input(data.get('last_name', '').strip())
            
            # Validation
            errors = []
            
            if not email:
                errors.append('Email is required')
            elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                errors.append('Invalid email format')
            elif User.query.filter_by(email=email).first():
                errors.append('Email already registered')
            
            if not username:
                errors.append('Username is required')
            elif len(username) < 3:
                errors.append('Username must be at least 3 characters')
            elif User.query.filter_by(username=username).first():
                errors.append('Username already taken')
            
            if not password:
                errors.append('Password is required')
            elif password != confirm_password:
                errors.append('Passwords do not match')
            else:
                # Password strength validation
                password_validation = validate_password_strength(password)
                if not password_validation['is_valid']:
                    errors.extend(password_validation['issues'])
            
            if not first_name:
                errors.append('First name is required')
            
            if not last_name:
                errors.append('Last name is required')
            
            if errors:
                return jsonify({
                    'error': 'Validation failed',
                    'message': 'Please fix the following errors',
                    'errors': errors
                }), 400
            
            # Create new user
            user = User(
                email=email,
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Log registration
            audit_log = AuditLog(
                user_id=user.id,
                action='user_registered',
                resource_type='user',
                resource_id=str(user.id),
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                endpoint=request.endpoint,
                status='success'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            logger.info(f"New user registered: {user.email}")
            
            # Auto-login user
            login_user(user)
            
            if request.is_json:
                return jsonify({
                    'message': 'Registration successful',
                    'user': user.to_dict(),
                    'redirect_url': url_for('dashboard')
                })
            else:
                flash('Registration successful! Welcome to Healthcare Chatbot.', 'success')
                return redirect(url_for('dashboard'))
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration: {str(e)}")
            return jsonify({
                'error': 'Registration failed',
                'message': 'An error occurred during registration'
            }), 500
    
    # GET request - show registration form
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout endpoint."""
    user_id = current_user.id
    user_email = current_user.email
    
    # Invalidate user cache
    invalidate_user_cache(str(user_id))
    
    # Clear session
    session.clear()
    
    # Logout user
    logout_user()
    
    # Log logout
    audit_log = AuditLog(
        user_id=user_id,
        action='logout',
        resource_type='user',
        resource_id=str(user_id),
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        endpoint=request.endpoint,
        status='success'
    )
    db.session.add(audit_log)
    db.session.commit()
    
    logger.info(f"User {user_email} logged out")
    
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management."""
    if request.method == 'POST':
        try:
            # Get form data
            data = request.get_json() if request.is_json else request.form
            
            # Update allowed fields
            allowed_fields = ['first_name', 'last_name', 'phone', 'date_of_birth']
            updated_fields = []
            
            for field in allowed_fields:
                if field in data:
                    new_value = sanitize_input(str(data[field]).strip())
                    if new_value != getattr(current_user, field, None):
                        setattr(current_user, field, new_value)
                        updated_fields.append(field)
            
            # Handle medical information updates
            if 'medical_history' in data:
                medical_history = data.get('medical_history', [])
                if isinstance(medical_history, list):
                    current_user.set_medical_history(medical_history)
                    updated_fields.append('medical_history')
            
            if 'allergies' in data:
                allergies = data.get('allergies', [])
                if isinstance(allergies, list):
                    current_user.set_allergies(allergies)
                    updated_fields.append('allergies')
            
            if 'medications' in data:
                medications = data.get('medications', [])
                if isinstance(medications, list):
                    current_user.set_medications(medications)
                    updated_fields.append('medications')
            
            # Update timestamp
            if updated_fields:
                current_user.updated_at = datetime.utcnow()
                db.session.commit()
                
                # Invalidate user cache
                invalidate_user_cache(str(current_user.id))
                
                # Log profile update
                audit_log = AuditLog(
                    user_id=current_user.id,
                    action='profile_updated',
                    resource_type='user',
                    resource_id=str(current_user.id),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    endpoint=request.endpoint,
                    status='success',
                    details=f"Updated fields: {', '.join(updated_fields)}"
                )
                db.session.add(audit_log)
                db.session.commit()
                
                logger.info(f"User {current_user.email} updated profile: {updated_fields}")
                
                if request.is_json:
                    return jsonify({
                        'message': 'Profile updated successfully',
                        'updated_fields': updated_fields
                    })
                else:
                    flash('Profile updated successfully!', 'success')
            else:
                if request.is_json:
                    return jsonify({'message': 'No changes made'})
                else:
                    flash('No changes made.', 'info')
                    
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {str(e)}")
            if request.is_json:
                return jsonify({
                    'error': 'Update failed',
                    'message': 'An error occurred while updating profile'
                }), 500
            else:
                flash('An error occurred while updating your profile.', 'error')
    
    # GET request or after POST - show profile
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    try:
        # Rate limiting
        user_id = str(current_user.id)
        if not rate_limiter.is_allowed(f"change_password:{user_id}", 3, 3600):
            return jsonify({
                'error': 'Too many password change attempts',
                'message': 'Please try again in an hour'
            }), 429
        
        # Get form data
        data = request.get_json() if request.is_json else request.form
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validation
        if not current_password:
            return jsonify({
                'error': 'Current password required',
                'message': 'Please enter your current password'
            }), 400
        
        if not current_user.check_password(current_password):
            return jsonify({
                'error': 'Invalid current password',
                'message': 'Current password is incorrect'
            }), 400
        
        if not new_password:
            return jsonify({
                'error': 'New password required',
                'message': 'Please enter a new password'
            }), 400
        
        if new_password != confirm_password:
            return jsonify({
                'error': 'Passwords do not match',
                'message': 'New password and confirmation do not match'
            }), 400
        
        # Password strength validation
        password_validation = validate_password_strength(new_password)
        if not password_validation['is_valid']:
            return jsonify({
                'error': 'Weak password',
                'message': 'Password does not meet requirements',
                'issues': password_validation['issues']
            }), 400
        
        # Update password
        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log password change
        audit_log = AuditLog(
            user_id=current_user.id,
            action='password_changed',
            resource_type='user',
            resource_id=str(current_user.id),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            endpoint=request.endpoint,
            status='success'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        logger.info(f"User {current_user.email} changed password")
        
        return jsonify({
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing password: {str(e)}")
        return jsonify({
            'error': 'Password change failed',
            'message': 'An error occurred while changing password'
        }), 500

@auth_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account."""
    try:
        # Get confirmation
        data = request.get_json() if request.is_json else request.form
        password = data.get('password', '')
        confirmation = data.get('confirmation', '')
        
        # Validation
        if not password:
            return jsonify({
                'error': 'Password required',
                'message': 'Please enter your password to confirm'
            }), 400
        
        if not current_user.check_password(password):
            return jsonify({
                'error': 'Invalid password',
                'message': 'Password is incorrect'
            }), 400
        
        if confirmation != 'DELETE':
            return jsonify({
                'error': 'Confirmation required',
                'message': 'Please type DELETE to confirm account deletion'
            }), 400
        
        user_id = current_user.id
        user_email = current_user.email
        
        # Log account deletion
        audit_log = AuditLog(
            user_id=user_id,
            action='account_deleted',
            resource_type='user',
            resource_id=str(user_id),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            endpoint=request.endpoint,
            status='success'
        )
        db.session.add(audit_log)
        
        # Soft delete - mark as inactive instead of hard delete
        current_user.is_active = False
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Invalidate user cache
        invalidate_user_cache(str(user_id))
        
        # Logout user
        logout_user()
        
        logger.info(f"User account deleted: {user_email}")
        
        return jsonify({
            'message': 'Account deleted successfully',
            'redirect_url': url_for('auth.login')
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting account: {str(e)}")
        return jsonify({
            'error': 'Account deletion failed',
            'message': 'An error occurred while deleting account'
        }), 500

@auth_bp.route('/check-email')
def check_email():
    """Check if email is available for registration."""
    email = request.args.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'available': False, 'message': 'Email is required'})
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'available': False, 'message': 'Invalid email format'})
    
    user = User.query.filter_by(email=email).first()
    available = user is None
    
    return jsonify({
        'available': available,
        'message': 'Email is available' if available else 'Email is already registered'
    })

@auth_bp.route('/check-username')
def check_username():
    """Check if username is available for registration."""
    username = request.args.get('username', '').strip()
    
    if not username:
        return jsonify({'available': False, 'message': 'Username is required'})
    
    if len(username) < 3:
        return jsonify({'available': False, 'message': 'Username must be at least 3 characters'})
    
    user = User.query.filter_by(username=username).first()
    available = user is None
    
    return jsonify({
        'available': available,
        'message': 'Username is available' if available else 'Username is already taken'
    })
