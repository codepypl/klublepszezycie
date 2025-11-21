"""
Dashboard Stats Service - oblicza statystyki dla dashboardu ankietera
"""
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
from sqlalchemy import func

from app.models import db, User
from app.models.stats_model import Stats
# CRM models removed - CRM module not used
# from app.services.twilio_service import TwilioVoIPService

logger = logging.getLogger(__name__)


class DashboardStatsService:
    """Serwis obliczania statystyk dla dashboardu ankietera"""
    
    def __init__(self):
        # Twilio service removed - CRM module not used
        pass
    
    def get_stats_for_ankieter(self, ankieter_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Pobiera wszystkie statystyki dla ankietera
        
        Args:
            ankieter_id: ID ankietera
            target_date: Data dla której pobierać statystyki (default: dziś)
            
        Returns:
            Dict ze wszystkimi 12 statystykami
        """
        try:
            if target_date is None:
                target_date = datetime.now().date()
            
            logger.info(f"📊 Obliczam statystyki dla ankietera {ankieter_id}, data: {target_date}")
            
            # 1. Pobierz statystyki z Twilio API (połączenia)
            twilio_stats = self._get_twilio_stats(ankieter_id, target_date)
            
            # 2. Pobierz statystyki z bazy danych
            db_stats = self._get_database_stats(ankieter_id, target_date)
            
            # 3. Merge i zwróć
            stats = {
                **twilio_stats,
                **db_stats,
                'timestamp': datetime.now().isoformat(),
                'date': target_date.isoformat()
            }
            
            logger.info(f"✅ Statystyki obliczone: {len(stats)} wskaźników")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Błąd obliczania statystyk: {e}")
            return self._get_empty_stats()
    
    def _get_twilio_stats(self, ankieter_id: int, target_date: date) -> Dict[str, int]:
        """
        Pobiera statystyki połączeń z Twilio API
        Note: CRM module removed - returns empty stats
        """
        return self._get_empty_twilio_stats()
    
    def _get_database_stats(self, ankieter_id: int, target_date: date) -> Dict[str, int]:
        """
        Oblicza statystyki z bazy danych
        Note: CRM module removed - returns empty stats
        """
        return {
            'leads_today': 0,
            'total_contacts': 0,
            'total_rescheduled': 0,
            'active_campaigns': 0
        }
    
    def update_stats_after_call(self, call_id: int) -> bool:
        """
        Aktualizuje statystyki w tabeli Stats po zakończeniu połączenia
        Note: CRM module removed - function disabled
        """
        logger.warning("⚠️  update_stats_after_call called but CRM module is removed")
        return False
    
    def _get_empty_stats(self) -> Dict[str, int]:
        """Zwraca puste statystyki (gdy błąd)"""
        return {
            **self._get_empty_twilio_stats(),
            'leads_today': 0,
            'total_contacts': 0,
            'total_rescheduled': 0,
            'active_campaigns': 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_work_time(self, ankieter_id: int, target_date: date) -> Dict[str, int]:
        """
        Oblicza czasy pracy na podstawie logów UserLogs
        
        Returns:
            Dict z czasami w sekundach: total_logged_time, total_work_time, total_break_time
        """
        from sqlalchemy import func
        from app.models.user_logs_model import UserLogs
        
        try:
            # Pobierz wszystkie logi pracy dla danego dnia
            work_logs = UserLogs.query.filter(
                UserLogs.user_id == ankieter_id,
                UserLogs.action_type.in_(['work_start', 'work_stop', 'break_start', 'break_end']),
                func.date(UserLogs.created_at) == target_date
            ).order_by(UserLogs.created_at).all()
            
            if not work_logs:
                return {'total_logged_time': 0, 'total_work_time': 0, 'total_break_time': 0}
            
            total_logged_time = 0
            total_break_time = 0
            current_work_start = None
            current_break_start = None
            
            for log in work_logs:
                if log.action_type == 'work_start':
                    current_work_start = log.created_at
                elif log.action_type == 'work_stop' and current_work_start:
                    # Oblicz czas od work_start do work_stop
                    work_duration = (log.created_at - current_work_start).total_seconds()
                    total_logged_time += work_duration
                    current_work_start = None
                elif log.action_type == 'break_start':
                    current_break_start = log.created_at
                elif log.action_type == 'break_end' and current_break_start:
                    # Oblicz czas przerwy
                    break_duration = (log.created_at - current_break_start).total_seconds()
                    total_break_time += break_duration
                    current_break_start = None
            
            # Jeśli sesja pracy nadal trwa (work_start bez work_stop)
            if current_work_start:
                now = datetime.now()
                if now.date() == target_date:
                    work_duration = (now - current_work_start).total_seconds()
                    total_logged_time += work_duration
            
            # Czas pracy = czas zalogowania - czas przerw
            total_work_time = total_logged_time - total_break_time
            
            return {
                'total_logged_time': int(total_logged_time),
                'total_work_time': int(total_work_time),
                'total_break_time': int(total_break_time)
            }
            
        except Exception as e:
            logger.error(f"❌ Błąd obliczania czasu pracy: {e}")
            return {'total_logged_time': 0, 'total_work_time': 0, 'total_break_time': 0}
    
    def _get_empty_twilio_stats(self) -> Dict[str, int]:
        """Zwraca puste statystyki Twilio"""
        return {
            'calls_total_today': 0,
            'calls_connected_today': 0,
            'calls_missed_today': 0,
            'total_call_time_today': 0,
            'average_call_time_today': 0,
            'total_work_time_today': 0,
            'total_logged_time_today': 0,
            'total_break_time_today': 0
        }

