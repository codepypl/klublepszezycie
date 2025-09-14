"""
Authentication routes blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User, PasswordResetToken
from app.utils.validation import validate_email
from datetime import datetime, timedelta
import secrets
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email i hasło są wymagane', 'error')
            return render_template('user/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.is_active:
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('public.index'))
            else:
                flash('Konto jest nieaktywne', 'error')
        else:
            flash('Nieprawidłowy email lub hasło', 'error')
    
    return render_template('user/login.html')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            flash('Wszystkie pola są wymagane', 'error')
            return render_template('user/change_password.html')
        
        if new_password != confirm_password:
            flash('Nowe hasła nie są identyczne', 'error')
            return render_template('user/change_password.html')
        
        # Validate password strength
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            flash(message, 'error')
            return render_template('user/change_password.html')
        
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Nieprawidłowe obecne hasło', 'error')
            return render_template('user/change_password.html')
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        current_user.is_temporary_password = False
        db.session.commit()
        
        flash('Hasło zostało zmienione pomyślnie', 'success')
        return redirect(url_for('auth.change_password'))
    
    return render_template('user/change_password.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Zostałeś wylogowany', 'info')
    return redirect(url_for('public.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('user/profile.html')

@auth_bp.route('/api/profile', methods=['GET', 'PUT'])
@login_required
def api_profile():
    """API for user profile management"""
    if request.method == 'GET':
        # Get current user profile
        user_dict = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'name': current_user.name,
            'phone': current_user.phone,
            'club_member': current_user.club_member,
            'is_active': current_user.is_active,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        }
        return jsonify({'success': True, 'user': user_dict})
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Update user profile fields
            if 'name' in data:
                current_user.name = data['name']
            if 'phone' in data:
                current_user.phone = data['phone']
            if 'email' in data:
                # Check if email is already taken by another user
                existing_user = User.query.filter_by(email=data['email']).first()
                if existing_user and existing_user.id != current_user.id:
                    return jsonify({'success': False, 'error': 'Ten email jest już używany przez innego użytkownika'}), 400
                current_user.email = data['email']
            if 'club_member' in data:
                current_user.club_member = data['club_member']
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Profil został zaktualizowany'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

def generate_password_reset_token():
    """Generate a secure random token for password reset"""
    return secrets.token_urlsafe(32)

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Hasło musi mieć co najmniej 8 znaków"
    
    if not re.search(r'[A-Z]', password):
        return False, "Hasło musi zawierać co najmniej jedną wielką literę"
    
    if not re.search(r'[a-z]', password):
        return False, "Hasło musi zawierać co najmniej jedną małą literę"
    
    if not re.search(r'\d', password):
        return False, "Hasło musi zawierać co najmniej jedną cyfrę"
    
    return True, "Hasło jest wystarczająco silne"

def send_password_reset_email(user, token):
    """Send password reset email to user"""
    try:
        from app.services.email_service import EmailService
        from urllib.parse import urljoin
        
        email_service = EmailService()
        
        # Create reset URL
        reset_url = urljoin(request.url_root, url_for('auth.reset_password', token=token))
        
        # Send email using template
        subject = "Resetowanie hasła - Klub Lepsze Życie"
        context = {
            'user_name': user.name or 'Użytkowniku',
            'reset_url': reset_url,
            'expires_hours': 24
        }
        
        success = email_service.send_template_email(
            template_name='password_reset',
            to_email=user.email,
            to_name=user.name,
            context=context
        )
        
        return success
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email jest wymagany', 'error')
            return render_template('user/forgot_password.html')
        
        if not validate_email(email):
            flash('Nieprawidłowy format email', 'error')
            return render_template('user/forgot_password.html')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate token
            token = generate_password_reset_token()
            
            # Create token record
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            # Remove any existing tokens for this user
            PasswordResetToken.query.filter_by(user_id=user.id).delete()
            
            db.session.add(reset_token)
            db.session.commit()
            
            # Send email
            if send_password_reset_email(user, token):
                flash('Link do resetowania hasła został wysłany na podany email', 'success')
            else:
                flash('Wystąpił błąd podczas wysyłania emaila. Spróbuj ponownie.', 'error')
        else:
            # Don't reveal if user exists or not for security
            flash('Jeśli konto z podanym emailem istnieje, link do resetowania hasła został wysłany', 'info')
        
        return redirect(url_for('auth.forgot_password'))
    
    return render_template('user/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    # Find token
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token or not reset_token.is_valid():
        flash('Link do resetowania hasła jest nieprawidłowy lub wygasł', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or not confirm_password:
            flash('Wszystkie pola są wymagane', 'error')
            return render_template('user/reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Nowe hasła nie są identyczne', 'error')
            return render_template('user/reset_password.html', token=token)
        
        # Validate password strength
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            flash(message, 'error')
            return render_template('user/reset_password.html', token=token)
        
        # Update password
        user = reset_token.user
        user.password_hash = generate_password_hash(new_password)
        user.is_temporary_password = False
        
        # Mark token as used
        reset_token.used = True
        
        db.session.commit()
        
        flash('Hasło zostało pomyślnie zresetowane. Możesz się teraz zalogować', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('user/reset_password.html', token=token)
