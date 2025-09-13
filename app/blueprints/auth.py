"""
Authentication routes blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User
from app.utils.validation import validate_email

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
        
        if len(new_password) < 6:
            flash('Hasło musi mieć co najmniej 6 znaków', 'error')
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
