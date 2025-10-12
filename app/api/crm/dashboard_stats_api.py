"""
Dashboard Stats API - endpoint dla statystyk dashboardu ankietera
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from app.utils.auth_utils import ankieter_required
from app.services.dashboard_stats_service import DashboardStatsService

# Create blueprint
dashboard_stats_api_bp = Blueprint('dashboard_stats_api', __name__)


@dashboard_stats_api_bp.route('/dashboard/stats', methods=['GET'])
@login_required
@ankieter_required
def get_dashboard_stats():
    """
    Pobiera statystyki dla dashboardu ankietera
    
    Query params:
        date (optional): Data w formacie YYYY-MM-DD (default: dziś)
    
    Returns:
        JSON z 12 statystykami
    """
    try:
        # Pobierz opcjonalną datę z parametrów
        date_param = request.args.get('date')
        target_date = None
        
        if date_param:
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Nieprawidłowy format daty. Użyj YYYY-MM-DD'
                }), 400
        
        # Pobierz statystyki
        service = DashboardStatsService()
        stats = service.get_stats_for_ankieter(current_user.id, target_date)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_stats_api_bp.route('/dashboard/stats/update-after-call', methods=['POST'])
@login_required
@ankieter_required
def update_stats_after_call():
    """
    Aktualizuje statystyki po zakończeniu połączenia
    
    Body:
        {
            "call_id": 123
        }
    
    Returns:
        JSON z wynikiem aktualizacji
    """
    try:
        data = request.get_json()
        
        if not data or 'call_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Brak call_id w żądaniu'
            }), 400
        
        call_id = data['call_id']
        
        # Aktualizuj statystyki
        service = DashboardStatsService()
        success = service.update_stats_after_call(call_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Statystyki zaktualizowane'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Nie udało się zaktualizować statystyk'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


