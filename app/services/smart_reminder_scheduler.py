"""
Inteligentny system planowania przypomnień o wydarzeniach
Optymalizuje wysyłanie e-maili aby uniknąć blokad Mailgun
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging
from app import db
from app.models import User, UserGroup, UserGroupMember, EventSchedule, EmailQueue, EmailLog
from app.utils.timezone_utils import get_local_now

class SmartReminderScheduler:
    """Inteligentny planista przypomnień"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Konfiguracja dla płatnego planu Mailgun
        self.max_emails_per_minute = 600  # 10 emaili na sekundę
        self.max_emails_per_hour = 10000
        self.batch_size = 50
        self.delay_between_batches = 1  # sekunda
        
    def schedule_event_reminders_smart(self, event_id: int) -> Tuple[bool, str]:
        """
        Planuje przypomnienia o wydarzeniu z inteligentnym rozłożeniem w czasie
        
        Args:
            event_id: ID wydarzenia
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie zostało znalezione"
            
            # SPRAWDŹ CZY PRZYPOMNIENIA JUŻ ZOSTAŁY ZAPLANOWANE
            if event.reminders_scheduled:
                self.logger.warning(f"⚠️ Przypomnienia dla wydarzenia {event_id} już zostały zaplanowane")
                return True, f"Przypomnienia dla wydarzenia {event_id} już zaplanowane"
            
            # Pobierz wszystkich uczestników
            participants = self._get_event_participants(event_id)
            if not participants:
                return False, "Brak uczestników wydarzenia"
            
            participants_count = len(participants)
            self.logger.info(f"📅 Planuję przypomnienia dla {participants_count} uczestników wydarzenia '{event.title}'")
            
            # OBLICZ CAŁKOWITĄ LICZBĘ EMAILI DO WYSŁANIA
            total_emails = participants_count * 3  # 3 przypomnienia na osobę
            self.logger.info(f"📊 Łączna liczba emaili do wysłania: {total_emails}")
            
            # SPRAWDŹ DZIENNY LIMIT
            today_start = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_sent = EmailLog.query.filter(
                EmailLog.sent_at >= today_start,
                EmailLog.status == 'sent'
            ).count()
            
            if today_sent + total_emails > 1000:  # Dzienny limit
                self.logger.warning(f"⚠️ Przekroczenie dziennego limitu: {today_sent + total_emails}/1000")
                return False, f"Przekroczenie dziennego limitu emaili: {today_sent + total_emails}/1000"
            
            # Zaplanuj przypomnienia z inteligentnym rozłożeniem
            reminder_schedules = [
                {'hours': 24, 'type': '24h', 'template': 'event_reminder_24h'},
                {'hours': 1, 'type': '1h', 'template': 'event_reminder_1h'},
                {'minutes': 5, 'type': '5min', 'template': 'event_reminder_5min'}
            ]
            
            total_scheduled = 0
            
            for schedule in reminder_schedules:
                scheduled_count = self._schedule_reminder_batch(
                    event, participants, schedule, participants_count
                )
                total_scheduled += scheduled_count
                
                self.logger.info(f"✅ Zaplanowano {scheduled_count} przypomnień typu {schedule['type']}")
            
            return True, f"Zaplanowano {total_scheduled} przypomnień dla {participants_count} uczestników"
            
        except Exception as e:
            self.logger.error(f"❌ Błąd planowania przypomnień: {e}")
            return False, f"Błąd planowania przypomnień: {str(e)}"
    
    def _get_event_participants(self, event_id: int) -> List[User]:
        """Pobiera wszystkich uczestników wydarzenia"""
        participants = set()
        
        # 1. Członkowie klubu
        club_group = UserGroup.query.filter_by(
            name="Członkowie klubu",
            group_type='club_members'
        ).first()
        
        if club_group:
            club_members = UserGroupMember.query.filter_by(
                group_id=club_group.id,
                is_active=True
            ).all()
            for member in club_members:
                user = User.query.get(member.user_id)
                if user and user.is_active:
                    participants.add(user)
        
        # 2. Członkowie grupy wydarzenia
        event_group = UserGroup.query.filter_by(
            name=f"Wydarzenie: {EventSchedule.query.get(event_id).title}",
            group_type='event_based'
        ).first()
        
        if event_group:
            event_members = UserGroupMember.query.filter_by(
                group_id=event_group.id,
                is_active=True
            ).all()
            for member in event_members:
                user = User.query.get(member.user_id)
                if user and user.is_active:
                    participants.add(user)
        
        return list(participants)
    
    def _schedule_reminder_batch(self, event: EventSchedule, participants: List[User], 
                                schedule: Dict, total_participants: int) -> int:
        """Planuje przypomnienia dla jednego typu z inteligentnym rozłożeniem"""
        try:
            # Oblicz docelowy czas przypomnienia
            if 'hours' in schedule:
                target_time = event.event_date - timedelta(hours=schedule['hours'])
            else:
                target_time = event.event_date - timedelta(minutes=schedule['minutes'])
            
            # Sprawdź czy nie jest za późno
            now = get_local_now()
            # Normalizuj timezone dla porównań
            if target_time.tzinfo is not None:
                target_time = target_time.replace(tzinfo=None)
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            
            if target_time <= now:
                self.logger.warning(f"⚠️ Za późno na przypomnienie {schedule['type']}")
                return 0
            
            # Oblicz optymalny czas rozpoczęcia wysyłki
            optimal_start_time = self._calculate_optimal_send_time(
                target_time, total_participants
            )
            
            if optimal_start_time <= now:
                self.logger.warning(f"⚠️ Optymalny czas wysyłki {schedule['type']} jest w przeszłości")
                return 0
            
            # Podziel uczestników na mniejsze grupy
            participant_batches = self._split_participants_into_batches(
                participants, self.batch_size
            )
            
            scheduled_count = 0
            
            # Zaplanuj każdą grupę z odpowiednim opóźnieniem
            for i, batch in enumerate(participant_batches):
                batch_send_time = optimal_start_time + timedelta(
                    seconds=i * self.delay_between_batches
                )
                
                # Dodaj emaile do kolejki z odpowiednim czasem
                for user in batch:
                    success = self._add_reminder_to_queue(
                        event, user, schedule, batch_send_time
                    )
                    if success:
                        scheduled_count += 1
            
            return scheduled_count
            
        except Exception as e:
            self.logger.error(f"❌ Błąd planowania przypomnień {schedule['type']}: {e}")
            return 0
    
    def _calculate_optimal_send_time(self, target_time: datetime, participants_count: int) -> datetime:
        """Oblicza optymalny czas rozpoczęcia wysyłki"""
        # Oblicz czas potrzebny na wysłanie wszystkich emaili
        batches_needed = (participants_count + self.batch_size - 1) // self.batch_size
        total_send_time = batches_needed * self.delay_between_batches
        
        # Dodaj 20% bufora na bezpieczeństwo
        total_send_time_with_buffer = int(total_send_time * 1.2)
        
        # Oblicz czas rozpoczęcia wysyłki
        return target_time - timedelta(seconds=total_send_time_with_buffer)
    
    def _split_participants_into_batches(self, participants: List[User], batch_size: int) -> List[List[User]]:
        """Dzieli uczestników na mniejsze grupy"""
        batches = []
        for i in range(0, len(participants), batch_size):
            batches.append(participants[i:i + batch_size])
        return batches
    
    def _add_reminder_to_queue(self, event: EventSchedule, user: User, 
                              schedule: Dict, send_time: datetime) -> bool:
        """Dodaje przypomnienie do kolejki"""
        try:
            from app.services.email_v2 import EmailManager
            email_manager = EmailManager()
            
            # Przygotuj kontekst
            context = {
                'event_title': event.title,
                'event_date': event.event_date.strftime('%d.%m.%Y'),
                'event_time': event.event_date.strftime('%H:%M'),
                'event_location': event.location or 'Online',
                'user_name': user.first_name,
                'event_id': event.id,
                'user_id': user.id
            }
            
            # Wyślij email przez EmailManager
            success, message = email_manager.send_template_email(
                to_email=user.email,
                template_name=schedule['template'],
                context=context,
                priority=2,
                scheduled_at=send_time,
                campaign_id=None
            )
            
            if not success and "duplikat" not in message.lower():
                self.logger.error(f"❌ Błąd dodawania przypomnienia dla {user.email}: {message}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Błąd dodawania przypomnienia: {e}")
            return False
