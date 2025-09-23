"""
Nowe endpointy dla unsubscribe i delete account z nowym systemem tokenów
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.services.unsubscribe_manager import unsubscribe_manager
from app import db
import logging

unsubscribe_v2_bp = Blueprint('unsubscribe_v2', __name__)

@unsubscribe_v2_bp.route('/unsubscribe/<token>')
def unsubscribe(token):
    """Obsługuje wypisanie z klubu"""
    
    # Weryfikuj token
    is_valid, user_data = unsubscribe_manager.verify_token(token)
    
    if not is_valid:
        return render_template('unsubscribe/error.html', 
                             error="Nieprawidłowy lub wygasły token",
                             message="Link do wypisania się jest nieprawidłowy lub wygasł. Tokeny są ważne przez 30 dni.")
    
    user = user_data['user']
    action = user_data['action']
    
    # Sprawdź czy to właściwa akcja
    if action != 'unsubscribe':
        return render_template('unsubscribe/error.html',
                             error="Nieprawidłowy token",
                             message="Ten token nie jest przeznaczony do wypisania się z klubu.")
    
    # Sprawdź czy użytkownik jest już wypisany z klubu
    if not user.club_member:
        return render_template('unsubscribe/success.html',
                             action="wypisanie z klubu",
                             message=f"Użytkownik {user.email} nie jest już członkiem klubu.",
                             user_email=user.email)
    
    # Pokaż stronę potwierdzenia
    return render_template('unsubscribe/confirm.html',
                         action="wypisanie z klubu",
                         message=f"Czy na pewno chcesz wypisać się z klubu?",
                         details=f"Użytkownik: {user.email}",
                         token=token,
                         user_email=user.email)

@unsubscribe_v2_bp.route('/unsubscribe/confirm', methods=['POST'])
def confirm_unsubscribe():
    """Potwierdza wypisanie z klubu"""
    token = request.form.get('token')
    
    if not token:
        flash('Brak tokenu autoryzacji', 'error')
        return redirect(url_for('unsubscribe_v2.unsubscribe', token=''))
    
    # Weryfikuj token ponownie
    is_valid, user_data = unsubscribe_manager.verify_token(token)
    
    if not is_valid:
        return render_template('unsubscribe/error.html',
                             error="Nieprawidłowy lub wygasły token",
                             message="Link do wypisania się jest nieprawidłowy lub wygasł.")
    
    user = user_data['user']
    
    # Przetwórz wypisanie
    success, message = unsubscribe_manager.process_unsubscribe(user)
    
    if success:
        return render_template('unsubscribe/success.html',
                             action="wypisanie z klubu",
                             message=message,
                             details=f"Użytkownik: {user.email}",
                             user_email=user.email)
    else:
        return render_template('unsubscribe/error.html',
                             error="Błąd wypisania",
                             message=message)

@unsubscribe_v2_bp.route('/delete-account/<token>')
def delete_account(token):
    """Obsługuje usunięcie konta"""
    
    # Weryfikuj token
    is_valid, user_data = unsubscribe_manager.verify_token(token)
    
    if not is_valid:
        return render_template('unsubscribe/error.html',
                             error="Nieprawidłowy lub wygasły token",
                             message="Link do usunięcia konta jest nieprawidłowy lub wygasł. Tokeny są ważne przez 30 dni.")
    
    user = user_data['user']
    action = user_data['action']
    
    # Sprawdź czy to właściwa akcja
    if action != 'delete_account':
        return render_template('unsubscribe/error.html',
                             error="Nieprawidłowy token",
                             message="Ten token nie jest przeznaczony do usunięcia konta.")
    
    # Pokaż stronę potwierdzenia
    return render_template('unsubscribe/confirm_delete.html',
                         action="usunięcie konta",
                         message=f"Czy na pewno chcesz usunąć swoje konto?",
                         details=f"Użytkownik: {user.email}",
                         warning="Ta operacja jest nieodwracalna! Wszystkie Twoje dane zostaną trwale usunięte.",
                         token=token,
                         user_email=user.email)

@unsubscribe_v2_bp.route('/delete-account/confirm', methods=['POST'])
def confirm_delete_account():
    """Potwierdza usunięcie konta"""
    token = request.form.get('token')
    confirmation = request.form.get('confirmation')
    
    if not token:
        flash('Brak tokenu autoryzacji', 'error')
        return redirect(url_for('unsubscribe_v2.delete_account', token=''))
    
    if confirmation != 'DELETE':
        return render_template('unsubscribe/error.html',
                             error="Nieprawidłowe potwierdzenie",
                             message="Musisz wpisać 'DELETE' aby potwierdzić usunięcie konta.")
    
    # Weryfikuj token ponownie
    is_valid, user_data = unsubscribe_manager.verify_token(token)
    
    if not is_valid:
        return render_template('unsubscribe/error.html',
                             error="Nieprawidłowy lub wygasły token",
                             message="Link do usunięcia konta jest nieprawidłowy lub wygasł.")
    
    user = user_data['user']
    user_email = user.email
    
    # Przetwórz usunięcie konta
    success, message = unsubscribe_manager.process_account_deletion(user)
    
    if success:
        return render_template('unsubscribe/success.html',
                             action="usunięcie konta",
                             message=message,
                             details=f"Użytkownik: {user_email}",
                             user_email=user_email)
    else:
        return render_template('unsubscribe/error.html',
                             error="Błąd usuwania konta",
                             message=message)

# API endpoints dla programistów/adminów
@unsubscribe_v2_bp.route('/api/unsubscribe/<email>')
def api_unsubscribe(email):
    """API endpoint do wypisania użytkownika (dla testów/adminów)"""
    try:
        from app.models.user_model import User
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        success, message = unsubscribe_manager.process_unsubscribe(user)
        
        return jsonify({
            'success': success,
            'message': message,
            'user_email': user.email
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@unsubscribe_v2_bp.route('/api/delete-account/<email>')
def api_delete_account(email):
    """API endpoint do usunięcia konta użytkownika (dla testów/adminów)"""
    try:
        from app.models.user_model import User
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        success, message = unsubscribe_manager.process_account_deletion(user)
        
        return jsonify({
            'success': success,
            'message': message,
            'user_email': user.email
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@unsubscribe_v2_bp.route('/api/generate-token/<email>/<action>')
def api_generate_token(email, action):
    """API endpoint do generowania tokenów (dla testów)"""
    try:
        if action not in ['unsubscribe', 'delete_account']:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
        token = unsubscribe_manager.generate_token(email, action)
        
        if not token:
            return jsonify({'success': False, 'error': 'Failed to generate token'}), 500
        
        return jsonify({
            'success': True,
            'token': token,
            'email': email,
            'action': action
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
