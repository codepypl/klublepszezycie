"""
Authentication business logic controller
"""
from flask import request, jsonify, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import db, User, PasswordResetToken
from app.utils.validation_utils import validate_email
from datetime import datetime, timedelta
import secrets
import re

class AuthController:
    """Authentication business logic controller"""
    
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate user with email and password"""
        try:
            if not email or not password:
                return {
                    'success': False,
                    'error': 'Email i hasło są wymagane'
                }
            
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password_hash, password):
                if user.is_active:
                    return {
                        'success': True,
                        'user': user
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Konto jest nieaktywne'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Nieprawidłowy email lub hasło'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def register_user(name, email, password, phone=None):
        """Register new user"""
        try:
            if not all([name, email, password]):
                return {
                    'success': False,
                    'error': 'Wszystkie pola są wymagane'
                }
            
            # Validate email
            if not validate_email(email):
                return {
                    'success': False,
                    'error': 'Nieprawidłowy format email'
                }
            
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                return {
                    'success': False,
                    'error': 'Użytkownik z tym emailem już istnieje'
                }
            
            # Create user
            user = User(
                name=name,
                email=email,
                phone=phone,
                password_hash=generate_password_hash(password),
                is_active=True,
                role='user'
            )
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'success': True,
                'user': user,
                'message': 'Konto zostało utworzone pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def change_password(old_password, new_password, confirm_password):
        """Change user password"""
        try:
            if not all([old_password, new_password, confirm_password]):
                return {
                    'success': False,
                    'error': 'Wszystkie pola są wymagane'
                }
            
            if new_password != confirm_password:
                return {
                    'success': False,
                    'error': 'Hasła nie są identyczne'
                }
            
            if len(new_password) < 6:
                return {
                    'success': False,
                    'error': 'Hasło musi mieć co najmniej 6 znaków'
                }
            
            # Verify old password
            if not check_password_hash(current_user.password_hash, old_password):
                return {
                    'success': False,
                    'error': 'Nieprawidłowe obecne hasło'
                }
            
            # Update password
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Hasło zostało zmienione pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def request_password_reset(email):
        """Request password reset"""
        try:
            if not email:
                return {
                    'success': False,
                    'error': 'Email jest wymagany'
                }
            
            user = User.query.filter_by(email=email).first()
            if not user:
                return {
                    'success': False,
                    'error': 'Użytkownik z tym emailem nie istnieje'
                }
            
            # Generate reset token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # Delete existing tokens for this user
            PasswordResetToken.query.filter_by(user_id=user.id).delete()
            
            # Create new token
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            
            db.session.add(reset_token)
            db.session.commit()
            
            return {
                'success': True,
                'token': token,
                'user': user,
                'message': 'Link do resetowania hasła został wysłany na email'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def reset_password(token, new_password, confirm_password):
        """Reset password with token"""
        try:
            if not all([token, new_password, confirm_password]):
                return {
                    'success': False,
                    'error': 'Wszystkie pola są wymagane'
                }
            
            if new_password != confirm_password:
                return {
                    'success': False,
                    'error': 'Hasła nie są identyczne'
                }
            
            if len(new_password) < 6:
                return {
                    'success': False,
                    'error': 'Hasło musi mieć co najmniej 6 znaków'
                }
            
            # Find valid token
            reset_token = PasswordResetToken.query.filter_by(
                token=token
            ).filter(PasswordResetToken.expires_at > datetime.utcnow()).first()
            
            if not reset_token:
                return {
                    'success': False,
                    'error': 'Nieprawidłowy lub wygasły token'
                }
            
            # Update password
            user = reset_token.user
            user.password_hash = generate_password_hash(new_password)
            
            # Delete used token
            db.session.delete(reset_token)
            db.session.commit()
            
            return {
                'success': True,
                'user': user,
                'message': 'Hasło zostało zresetowane pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_user_profile(user_id):
        """Get user profile"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'Użytkownik nie został znaleziony'
                }
            
            return {
                'success': True,
                'user': user
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_user_profile(user_id, name=None, phone=None, email=None):
        """Update user profile"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'Użytkownik nie został znaleziony'
                }
            
            if name:
                user.first_name = name
            if phone:
                user.phone = phone
            if email:
                # Check if email is already taken
                existing_user = User.query.filter(User.email == email, User.id != user_id).first()
                if existing_user:
                    return {
                        'success': False,
                        'error': 'Email jest już używany przez innego użytkownika'
                    }
                user.email = email
            
            db.session.commit()
            
            return {
                'success': True,
                'user': user,
                'message': 'Profil został zaktualizowany pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
