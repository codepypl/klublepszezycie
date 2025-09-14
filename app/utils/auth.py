"""
Authentication utility functions
"""
from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user
from models import User

def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin_role():
            flash('Brak uprawnień administratora do tej strony', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

def ankieter_required(f):
    """Decorator to require ankieter role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not (current_user.is_ankieter_role() or current_user.is_admin_role()):
            flash('Brak uprawnień ankietera do tej strony', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

def crm_required(f):
    """Decorator to require CRM access (ankieter or admin role)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not (current_user.is_ankieter_role() or current_user.is_admin_role()):
            flash('Brak uprawnień do systemu CRM', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """Decorator factory to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not current_user.has_role(role_name):
                flash(f'Brak uprawnień {role_name} do tej strony', 'error')
                return redirect(url_for('public.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

