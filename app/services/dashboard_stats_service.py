"""
Dashboard Stats Service - oblicza statystyki dla dashboardu ankietera
"""
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
from sqlalchemy import func

from app.models import db, User
from app.models.crm_model import Call, Contact, Campaign
from app.models.stats_model import Stats
from app.services.twilio_service import TwilioVoIPService

logger = logging.getLogger(__name__)


class DashboardStatsService:
    """Serwis obliczania statystyk dla dashboardu ankietera"""
    
    def __init__(self):
        self.twilio_service = TwilioVoIPService()
    
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
        
        Returns:
            Dict z statystykami połączeń
        """
        try:
            # Pobierz wszystkie call_sid z bazy dla danego dnia
            calls = Call.query.filter(
                Call.ankieter_id == ankieter_id,
                func.date(Call.call_date) == target_date
            ).all()
            
            if not calls:
                logger.info(f"ℹ️  Brak połączeń dla ankietera {ankieter_id} w dniu {target_date}")
                return self._get_empty_twilio_stats()
            
            logger.info(f"📞 Pobieranie szczegółów {len(calls)} połączeń z Twilio API...")
            
            total_calls = 0
            connected_calls = 0
            missed_calls = 0
            total_duration = 0
            
            for call in calls:
                if call.twilio_sid:
                    # Pobierz szczegóły z Twilio API
                    details = self.twilio_service.get_call_details(call.twilio_sid)
                    
                    if details:
                        total_calls += 1
                        status = details.get('status', '')
                        duration = details.get('duration', 0)
                        
                        if status == 'completed':
                            connected_calls += 1
                            total_duration += duration
                        elif status in ['busy', 'no-answer', 'failed', 'canceled']:
                            missed_calls += 1
            
            # Oblicz średni czas rozmowy
            average_duration = total_duration / connected_calls if connected_calls > 0 else 0
            
            return {
                'calls_total_today': total_calls,
                'calls_connected_today': connected_calls,
                'calls_missed_today': missed_calls,
                'total_call_time_today': total_duration,
                'average_call_time_today': round(average_duration, 2),
                'total_work_time_today': total_duration,  # Czas rozmów = czas pracy (można rozszerzyć)
                'total_logged_time_today': total_duration,  # TODO: tracking sesji logowania
                'total_break_time_today': 0  # TODO: tracking przerw
            }
            
        except Exception as e:
            logger.error(f"❌ Błąd pobierania statystyk z Twilio: {e}")
            return self._get_empty_twilio_stats()
    
    def _get_database_stats(self, ankieter_id: int, target_date: date) -> Dict[str, int]:
        """
        Oblicza statystyki z bazy danych i zapisuje do tabeli Stats
        
        Returns:
            Dict z statystykami z bazy
        """
        try:
            # 1. Leady dzisiaj
            leads = Call.query.filter(
                Call.ankieter_id == ankieter_id,
                func.date(Call.call_date) == target_date,
                Call.status == 'lead'
            ).count()
            
            # Zapisz leady do Stats (cache)
            Stats.set_value(
                stat_type='ankieter_leads_daily',
                value=leads,
                related_id=ankieter_id,
                related_type='ankieter',
                date_period=target_date
            )
            
            # 2. Łączna ilość kontaktów przypisanych do ankietera
            total_contacts = Contact.query.filter(
                Contact.assigned_ankieter_id == ankieter_id,
                Contact.is_active == True
            ).count()
            
            # 3. Ilość przeplanowań (business_reason='przełożenie')
            total_rescheduled = Contact.query.filter(
                Contact.assigned_ankieter_id == ankieter_id,
                Contact.business_reason == 'przełożenie'
            ).count()
            
            # 4. Ilość aktywnych kampanii
            active_campaigns = Campaign.query.filter(
                Campaign.is_active == True
            ).count()
            
            return {
                'leads_today': leads,
                'total_contacts': total_contacts,
                'total_rescheduled': total_rescheduled,
                'active_campaigns': active_campaigns
            }
            
        except Exception as e:
            logger.error(f"❌ Błąd obliczania statystyk z bazy: {e}")
            return {
                'leads_today': 0,
                'total_contacts': 0,
                'total_rescheduled': 0,
                'active_campaigns': 0
            }
    
    def update_stats_after_call(self, call_id: int) -> bool:
        """
        Aktualizuje statystyki w tabeli Stats po zakończeniu połączenia
        
        Args:
            call_id: ID połączenia
            
        Returns:
            True jeśli sukces
        """
        try:
            call = Call.query.get(call_id)
            if not call:
                logger.warning(f"⚠️  Call {call_id} nie znaleziony")
                return False
            
            call_date = call.call_date.date()
            ankieter_id = call.ankieter_id
            
            # Increment licznika połączeń
            Stats.increment(
                stat_type='ankieter_calls_daily',
                related_id=ankieter_id,
                related_type='ankieter',
                date_period=call_date
            )
            
            # Jeśli lead, increment leadów
            if call.status == 'lead':
                Stats.increment(
                    stat_type='ankieter_leads_daily',
                    related_id=ankieter_id,
                    related_type='ankieter',
                    date_period=call_date
                )
                logger.info(f"✅ Zaktualizowano statystyki - nowy lead dla ankietera {ankieter_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Błąd aktualizacji statystyk po połączeniu: {e}")
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

