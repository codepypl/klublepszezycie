"""
Authentication routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        result = AuthController.authenticate_user(email, password)
        
        if result['success']:
            login_user(result['user'])
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            # Redirect based on user role
            if result['user'].is_ankieter_role():
                return redirect(url_for('ankieter.dashboard'))
            elif result['user'].is_admin_role():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('public.index'))
        else:
            flash(result['error'], 'error')
    
    return render_template('user/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        
        if password != confirm_password:
            flash('Hasła nie są identyczne', 'error')
        else:
            result = AuthController.register_user(name, email, password, phone)
            
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('auth.login'))
            else:
                flash(result['error'], 'error')
    
    return render_template('user/register.html')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        result = AuthController.change_password(current_user, old_password, new_password, confirm_password)
        
        if result['success']:
            flash(result['message'], 'success')
            # Logout user after password change
            logout_user()
            return redirect(url_for('public.index'))
        else:
            flash(result['error'], 'error')
    
    return render_template('user/change_password.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        result = AuthController.request_password_reset(email)
        
        if result['success']:
            # Send email with reset link
            from app.services.email_service import EmailService
            email_service = EmailService()
            
            reset_url = url_for('auth.reset_password', token=result['token'], _external=True)
            
            email_service.send_template_email(
                to_email=result['user'].email,
                template_name='password_reset',
                context={'reset_url': reset_url},
                to_name=result['user'].first_name
            )
            
            flash(result['message'], 'success')
        else:
            flash(result['error'], 'error')
    
    return render_template('user/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        result = AuthController.reset_password(token, new_password, confirm_password)
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result['error'], 'error')
    
    return render_template('user/reset_password.html', token=token)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Zostałeś wylogowany', 'info')
    return redirect(url_for('public.index'))