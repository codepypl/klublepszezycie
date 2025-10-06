"""
Event Monitor Service - monitorowanie zmian wydarzeń w czasie rzeczywistym
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from app import create_app, db
from app.models import EventSchedule, User, UserGroup, UserGroupMember, EmailQueue
from app.services.email_v2 import EmailManager
from app.utils.timezone_utils import get_local_now

logger = logging.getLogger(__name__)

class EventMonitorService:
    """Serwis do monitorowania zmian wydarzeń i automatycznej aktualizacji kolejki"""
    
    def __init__(self):
        self.app = create_app()
        self.email_manager = EmailManager()
    
    def monitor_event_changes(self) -> Dict[str, Any]:
        """
        Monitoruje zmiany w wydarzeniach i aktualizuje kolejkę emaili
        
        Returns:
            Dict[str, Any]: Raport z monitorowania
        """
        try:
            with self.app.app_context():
                logger.info("🔍 Rozpoczynam monitorowanie zmian wydarzeń...")
                
                # Pobierz wszystkie aktywne wydarzenia
                events = EventSchedule.query.filter_by(is_active=True).all()
                
                updated_events = []
                errors = []
                
                for event in events:
                    try:
                        # Sprawdź czy wydarzenie wymaga aktualizacji
                        needs_update, reason = self._check_event_needs_update(event)
                        
                        if needs_update:
                            logger.info(f"🔄 Aktualizacja wydarzenia {event.id}: {reason}")
                            
                            # Aktualizuj powiadomienia dla wydarzenia
                            success, message = self._update_event_reminders(event)
                            
                            if success:
                                updated_events.append({
                                    'event_id': event.id,
                                    'title': event.title,
                                    'reason': reason,
                                    'message': message
                                })
                                logger.info(f"✅ Zaktualizowano wydarzenie {event.id}: {message}")
                            else:
                                errors.append({
                                    'event_id': event.id,
                                    'title': event.title,
                                    'error': message
                                })
                                logger.error(f"❌ Błąd aktualizacji wydarzenia {event.id}: {message}")
                        else:
                            logger.debug(f"ℹ️ Wydarzenie {event.id} nie wymaga aktualizacji")
                            
                    except Exception as e:
                        error_msg = f"Błąd monitorowania wydarzenia {event.id}: {str(e)}"
                        errors.append({
                            'event_id': event.id,
                            'title': event.title,
                            'error': error_msg
                        })
                        logger.error(f"❌ {error_msg}")
                
                logger.info(f"✅ Zakończono monitorowanie: {len(updated_events)} zaktualizowanych, {len(errors)} błędów")
                
                return {
                    'success': True,
                    'updated_events': updated_events,
                    'errors': errors,
                    'total_events': len(events),
                    'updated_count': len(updated_events),
                    'error_count': len(errors)
                }
                
        except Exception as e:
            logger.error(f"❌ Błąd monitorowania wydarzeń: {e}")
            return {
                'success': False,
                'error': str(e),
                'updated_events': [],
                'errors': []
            }
    
    def _check_event_needs_update(self, event: EventSchedule) -> Tuple[bool, str]:
        """
        Sprawdza czy wydarzenie wymaga aktualizacji powiadomień
        
        Args:
            event: Wydarzenie do sprawdzenia
            
        Returns:
            Tuple[bool, str]: (czy wymaga aktualizacji, powód)
        """
        try:
            # Sprawdź czy są powiadomienia w kolejce (wszystkie statusy)
            existing_reminders = EmailQueue.query.filter_by(
                event_id=event.id
            ).all()
            
            if not existing_reminders:
                # Brak powiadomień - sprawdź czy powinny być
                if not event.reminders_scheduled:
                    return True, "Brak zaplanowanych powiadomień"
                return False, "Brak powiadomień w kolejce"
            
            # Sprawdź czy powiadomienia są aktualne względem daty wydarzenia
            for reminder in existing_reminders:
                if not reminder.scheduled_at:
                    continue
                
                # Sprawdź czy powiadomienie jest zaplanowane na odpowiedni czas
                expected_time = self._calculate_expected_reminder_time(event, reminder)
                
                if expected_time:
                    # Normalizuj timezone dla porównania
                    scheduled_naive = reminder.scheduled_at.replace(tzinfo=None) if reminder.scheduled_at.tzinfo else reminder.scheduled_at
                    expected_naive = expected_time.replace(tzinfo=None) if expected_time.tzinfo else expected_time
                    
                    if abs((scheduled_naive - expected_naive).total_seconds()) > 300:  # 5 minut tolerancji
                        return True, f"Powiadomienie {reminder.id} ma nieaktualny czas: {reminder.scheduled_at} vs {expected_time}"
            
            # Sprawdź czy liczba powiadomień odpowiada liczbie uczestników
            # participants = self._get_event_participants(event.id)
            # expected_reminder_count = len(participants) * self._get_expected_reminder_types_count(event)
            
            # if len(existing_reminders) != expected_reminder_count:
            #     return True, f"Nieprawidłowa liczba powiadomień: {len(existing_reminders)} vs {expected_reminder_count}"
            
            # Nie sprawdzaj strategii - to powoduje zbyt częste usuwanie przypomnień
            # Po naprawie błędu timezone, powiadomienia powinny być stabilne
            
            return False, "Powiadomienia są aktualne"
            
        except Exception as e:
            logger.error(f"❌ Błąd sprawdzania wydarzenia {event.id}: {e}")
            return True, f"Błąd sprawdzania: {str(e)}"
    
    def _calculate_expected_reminder_time(self, event: EventSchedule, reminder: EmailQueue) -> Optional[datetime]:
        """
        Oblicza oczekiwany czas powiadomienia na podstawie typu
        
        Args:
            event: Wydarzenie
            reminder: Powiadomienie
            
        Returns:
            Optional[datetime]: Oczekiwany czas powiadomienia
        """
        try:
            template_name = reminder.template_name or ''
            
            if '24h' in template_name:
                return event.event_date - timedelta(hours=24)
            elif '1h' in template_name:
                return event.event_date - timedelta(hours=1)
            elif '5min' in template_name:
                return event.event_date - timedelta(minutes=5)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Błąd obliczania czasu powiadomienia: {e}")
            return None
    
    def _get_expected_reminder_types_count(self, event: EventSchedule) -> int:
        """
        Oblicza oczekiwaną liczbę typów powiadomień dla wydarzenia
        
        Args:
            event: Wydarzenie
            
        Returns:
            int: Liczba typów powiadomień
        """
        try:
            # Domyślnie 2 typy: 1h i 5min przed
            return 2
        except Exception as e:
            logger.error(f"❌ Błąd obliczania typów powiadomień: {e}")
            return 2  # Domyślnie 2 typy
    
    def _update_event_reminders(self, event: EventSchedule) -> Tuple[bool, str]:
        """
        Aktualizuje powiadomienia dla wydarzenia
        
        Args:
            event: Wydarzenie
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            # Usuń stare powiadomienia
            old_reminders = EmailQueue.query.filter_by(
                event_id=event.id,
                status='pending'
            ).all()
            
            for reminder in old_reminders:
                db.session.delete(reminder)
            
            logger.info(f"🗑️ Usunięto {len(old_reminders)} starych powiadomień dla wydarzenia {event.id}")
            
            # Resetuj flagę
            event.reminders_scheduled = False
            db.session.commit()
            
            # Zaplanuj nowe powiadomienia
            success, message = self.email_manager.send_event_reminders(event.id)
            
            if success:
                logger.info(f"✅ Zaplanowano nowe powiadomienia dla wydarzenia {event.id}: {message}")
                return True, f"Zaktualizowano powiadomienia: {message}"
            else:
                logger.error(f"❌ Błąd planowania powiadomień dla wydarzenia {event.id}: {message}")
                return False, f"Błąd planowania powiadomień: {message}"
                
        except Exception as e:
            logger.error(f"❌ Błąd aktualizacji powiadomień dla wydarzenia {event.id}: {e}")
            return False, f"Błąd aktualizacji: {str(e)}"
    
    def _get_event_participants(self, event_id: int) -> List[User]:
        """
        Pobiera uczestników wydarzenia
        
        Args:
            event_id: ID wydarzenia
            
        Returns:
            List[User]: Lista uczestników
        """
        try:
            # Pobierz uczestników z rejestracji
            participants = User.query.filter_by(
                event_id=event_id,
                account_type='event_registration'
            ).all()
            
            # Pobierz członków klubu (automatycznie zapisani na wszystkie wydarzenia)
            club_members = User.query.filter_by(
                club_member=True,
                is_active=True
            ).all()
            
            # Połącz listy (usuń duplikaty)
            all_participants = participants.copy()
            participant_emails = {p.email for p in participants}
            
            for member in club_members:
                if member.email not in participant_emails:
                    all_participants.append(member)
            
            return all_participants
            
        except Exception as e:
            logger.error(f"❌ Błąd pobierania uczestników wydarzenia {event_id}: {e}")
            return []
    
    def monitor_member_changes(self) -> Dict[str, Any]:
        """
        Monitoruje zmiany w członkach klubu i uczestnikach wydarzeń
        
        Returns:
            Dict[str, Any]: Raport z monitorowania
        """
        try:
            with self.app.app_context():
                logger.info("🔍 Rozpoczynam monitorowanie zmian członków...")
                
                # Sprawdź nowych członków klubu
                new_club_members = self._check_new_club_members()
                
                # Sprawdź nowych uczestników wydarzeń
                new_event_participants = self._check_new_event_participants()
                
                # Sprawdź usuniętych członków
                removed_members = self._check_removed_members()
                
                # Aktualizuj powiadomienia dla nowych członków
                updated_events = []
                for event_id in new_club_members + new_event_participants:
                    try:
                        event = EventSchedule.query.get(event_id)
                        if event and event.is_active:
                            success, message = self.email_manager.send_event_reminders_for_new_members(event_id)
                            if success:
                                updated_events.append({
                                    'event_id': event_id,
                                    'title': event.title,
                                    'message': message
                                })
                    except Exception as e:
                        logger.error(f"❌ Błąd aktualizacji powiadomień dla wydarzenia {event_id}: {e}")
                
                logger.info(f"✅ Zakończono monitorowanie członków: {len(updated_events)} zaktualizowanych wydarzeń")
                
                return {
                    'success': True,
                    'new_club_members': new_club_members,
                    'new_event_participants': new_event_participants,
                    'removed_members': removed_members,
                    'updated_events': updated_events
                }
                
        except Exception as e:
            logger.error(f"❌ Błąd monitorowania członków: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_new_club_members(self) -> List[int]:
        """Sprawdza nowych członków klubu"""
        # Implementacja sprawdzania nowych członków
        return []
    
    def _check_new_event_participants(self) -> List[int]:
        """Sprawdza nowych uczestników wydarzeń"""
        # Implementacja sprawdzania nowych uczestników
        return []
    
    def _check_removed_members(self) -> List[int]:
        """Sprawdza usuniętych członków"""
        # Implementacja sprawdzania usuniętych członków
        return []
