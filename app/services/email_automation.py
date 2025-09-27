"""
Email automation service for Lepsze Życie Club
"""
from datetime import datetime, timedelta
from app import db
from app.models import User, UserGroup, UserGroupMember, EventSchedule, EmailReminder
from app.services.mailgun_service import EnhancedNotificationProcessor
from app.utils.timezone_utils import get_local_now
from app.utils.token_utils import generate_unsubscribe_token, encrypt_email

class EmailAutomation:
    """Automatyzacje emailowe"""
    
    def __init__(self):
        self.email_processor = None
        self.email_service = None
    
    def _get_email_processor(self):
        """Lazy loading dla email_processor"""
        if self.email_processor is None:
            self.email_processor = EnhancedNotificationProcessor()
        return self.email_processor
    
    def _get_email_service(self):
        """Lazy loading dla email_service"""
        if self.email_service is None:
            from app.services.email_service import EmailService
            self.email_service = EmailService()
        return self.email_service
    
    def on_user_joined_club(self, user_id):
        """Wywoływane przy dołączeniu do klubu"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "Użytkownik nie został znaleziony"
            
            # Sprawdź czy użytkownik już jest w grupie klubu
            club_group = UserGroup.query.filter_by(
                name="Członkowie klubu",
                group_type='club_members'
            ).first()
            
            if not club_group:
                # Utwórz grupę klubu jeśli nie istnieje
                club_group = UserGroup(
                    name="Członkowie klubu",
                    group_type='club_members',
                    description="Wszyscy członkowie klubu"
                )
                db.session.add(club_group)
                db.session.commit()
            
            # Sprawdź czy użytkownik już jest członkiem
            existing_member = UserGroupMember.query.filter_by(
                user_id=user_id,
                group_id=club_group.id
            ).first()
            
            if existing_member:
                if not existing_member.is_active:
                    existing_member.is_active = True
                    db.session.commit()
                return True, "Użytkownik już jest członkiem klubu"
            
            # Dodaj użytkownika do grupy klubu
            member = UserGroupMember(
                user_id=user_id,
                group_id=club_group.id,
                is_active=True
            )
            db.session.add(member)
            db.session.commit()
            
            return True, "Użytkownik dodany do klubu"
            
        except Exception as e:
            return False, f"Błąd dodawania do klubu: {str(e)}"
    
    def schedule_event_reminders(self, event_id, group_type='event_based'):
        """Planuje przypomnienia o wydarzeniu"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie zostało znalezione"
            
            # Sprawdź czy przypomnienia już zostały zaplanowane dla tego wydarzenia
            from app.services.celery_cleanup import CeleryCleanupService
            existing_tasks = CeleryCleanupService.get_scheduled_event_tasks(event_id)
            
            if existing_tasks:
                print(f"⚠️ Przypomnienia już zaplanowane dla wydarzenia {event_id} - pomijam duplikaty")
                return True, f"Przypomnienia już zaplanowane ({len(existing_tasks)} zadań)"
            
            # Użyj inteligentnego planowania - sprawdzi członków klubu i wydarzenia
            return self.schedule_event_reminders_smart(event_id, group_type)
            
        except Exception as e:
            return False, f"Błąd planowania przypomnień: {str(e)}"
    
    def schedule_event_reminders_smart(self, event_id, group_type='event_based', participants_count=None):
        """Planuje przypomnienia o wydarzeniu z inteligentnym planowaniem czasu"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie zostało znalezione"
            
            # Pobierz członków z obu grup: klubu i wydarzenia (jak w send_event_reminder_task)
            all_members = set()  # Używamy set() aby uniknąć duplikatów
            
            # 1. Pobierz członków klubu
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
                    all_members.add(member.user_id)
                print(f"👥 Znaleziono {len(club_members)} członków klubu")
            
            # 2. Pobierz członków grupy wydarzenia (jeśli istnieje)
            event_group = UserGroup.query.filter_by(
                name=f"Wydarzenie: {event.title}",
                group_type='event_based'
            ).first()
            
            if event_group:
                event_members = UserGroupMember.query.filter_by(
                    group_id=event_group.id, 
                    is_active=True
                ).all()
                for member in event_members:
                    all_members.add(member.user_id)
                print(f"📅 Znaleziono {len(event_members)} członków grupy wydarzenia")
            
            if not all_members:
                return False, "Brak członków w żadnej grupie"
            
            # Użyj podanej liczby uczestników lub policz
            if participants_count is None:
                participants_count = len(all_members)
            
            # Zaplanuj przypomnienia z inteligentnym planowaniem
            reminders_scheduled = 0
            
            # Convert event date to timezone-aware for comparison
            if event.event_date.tzinfo is None:
                # Jeśli data nie ma strefy czasowej, traktuj ją jako lokalną
                from app.utils.timezone_utils import get_local_timezone
                tz = get_local_timezone()
                event_date_aware = tz.localize(event.event_date)
            else:
                event_date_aware = event.event_date
            
            now = get_local_now()
            
            # Inteligentne planowanie - oblicz optymalny czas wysyłki
            email_service = self._get_email_service()
            
            # Dla 600 uczestników: 600/50 = 12 paczek, 12*50*1s = 600s = 10min + 20% bufora = 12min
            # Więc zamiast wysyłać dokładnie 2h przed, wysyłamy 2h12min przed
            batch_size = 50
            delay_per_email = 1  # sekunda między emailami
            
            # Zaplanuj przypomnienia z inteligentnym czasem
            reminder_schedules = [
                {'hours': 24, 'type': '24h'},
                {'hours': 1, 'type': '1h'},
                {'minutes': 5, 'type': '5min'}
            ]
            
            for schedule in reminder_schedules:
                if 'hours' in schedule:
                    target_time = event_date_aware - timedelta(hours=schedule['hours'])
                else:
                    target_time = event_date_aware - timedelta(minutes=schedule['minutes'])
                
                # Oblicz optymalny czas rozpoczęcia wysyłki
                optimal_send_time = email_service.calculate_send_time(
                    target_time, 
                    participants_count, 
                    batch_size, 
                    delay_per_email
                )
                
                # Sprawdź czy nie jest za późno - porównaj z target_time, nie z optimal_send_time
                if target_time.replace(tzinfo=None) < now.replace(tzinfo=None):
                    print(f"⚠️ Za późno na przypomnienie {schedule['type']} przed wydarzeniem")
                    continue
                
                # Dodatkowe zabezpieczenie - sprawdź czy optimal_send_time nie jest w przeszłości
                if optimal_send_time.replace(tzinfo=None) < now.replace(tzinfo=None):
                    print(f"⚠️ Optymalny czas wysyłki {schedule['type']} jest w przeszłości - pomijam")
                    continue
                
                print(f"📅 Zaplanowano przypomnienie {schedule['type']}: {optimal_send_time} (docelowo: {target_time})")
                
                # Zaplanuj wysyłkę przez Celery
                try:
                    from app.tasks.email_tasks import send_event_reminder_task
                    send_event_reminder_task.apply_async(
                        args=[event_id, schedule['type'], group_type],
                        eta=optimal_send_time
                    )
                except ImportError:
                    print(f"⚠️ Celery niedostępny - przypomnienie {schedule['type']} nie zostało zaplanowane")
                
                reminders_scheduled += 1
            
            return True, f"Zaplanowano {reminders_scheduled} przypomnień dla {participants_count} uczestników"
            
        except Exception as e:
            return False, f"Błąd planowania przypomnień: {str(e)}"
    
    def update_event_notifications(self, event_id, old_event_date, new_event_date):
        """Aktualizuje powiadomienia po zmianie godziny wydarzenia"""
        try:
            from app.models import EmailReminder, EmailQueue
            
            # Uruchom zadanie Celery do aktualizacji powiadomień (tymczasowo wyłączone)
            try:
                from app.tasks.email_tasks import update_event_notifications_task
                task = update_event_notifications_task.delay(
                    event_id, 
                    old_event_date.isoformat(), 
                    new_event_date.isoformat()
                )
                return True, f"Zadanie aktualizacji powiadomień uruchomione (ID: {task.id})"
            except ImportError:
                print("⚠️ Celery niedostępny - aktualizacja powiadomień nie została zaplanowana")
                return True, "Celery niedostępny - aktualizacja powiadomień pominięta"
            
        except Exception as e:
            return False, f"Błąd aktualizacji powiadomień: {str(e)}"
    
    def process_event_reminders(self):
        """Przetwarza przypomnienia o wydarzeniach (wywoływane przez cron)"""
        try:
            # Znajdź wydarzenia w najbliższych 25 godzinach
            now = get_local_now()
            future_events = EventSchedule.query.filter(
                EventSchedule.is_active == True,
                EventSchedule.is_published == True,
                EventSchedule.event_date > now.replace(tzinfo=None),
                EventSchedule.event_date <= (now + timedelta(hours=25)).replace(tzinfo=None)
            ).all()
            
            processed = 0
            
            for event in future_events:
                try:
                    # Zaplanuj przypomnienia dla tego wydarzenia
                    success, message = self.schedule_event_reminders(event.id)
                    if success:
                        processed += 1
                        print(f"✅ Zaplanowano przypomnienia dla wydarzenia: {event.title}")
                    else:
                        print(f"❌ Błąd planowania przypomnień dla {event.title}: {message}")
                        
                except Exception as e:
                    print(f"❌ Błąd przetwarzania wydarzenia {event.id}: {str(e)}")
            
            return True, f"Przetworzono {processed} wydarzeń"
            
        except Exception as e:
            return False, f"Błąd przetwarzania przypomnień: {str(e)}"
    
    def archive_old_events(self, days_old=30):
        """Archiwizuje stare wydarzenia"""
        try:
            cutoff_date = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now() - timedelta(days=days_old)
            
            old_events = EventSchedule.query.filter(
                EventSchedule.event_date < cutoff_date,
                EventSchedule.is_active == True
            ).all()
            
            archived_count = 0
            for event in old_events:
                event.is_active = False
                archived_count += 1
            
            db.session.commit()
            
            return True, f"Zarchiwizowano {archived_count} wydarzeń"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Błąd archiwizowania wydarzeń: {str(e)}"
    
    def archive_ended_events(self):
        """Archiwizuje zakończone wydarzenia i czyści grupy"""
        try:
            from app.models import EventSchedule
            
            # Znajdź zakończone wydarzenia
            ended_events = []
            all_events = EventSchedule.query.filter(
                EventSchedule.is_active == True,
                EventSchedule.is_published == True
            ).all()
            
            for event in all_events:
                if event.is_ended():
                    ended_events.append(event)
            
            archived_count = 0
            for event in ended_events:
                # Użyj metody archive() z modelu EventSchedule
                success, message = event.archive()
                if success:
                    archived_count += 1
                    print(f"✅ Zarchiwizowano: {event.title}")
                else:
                    print(f"❌ Błąd archiwizacji {event.title}: {message}")
            
            # Loguj operację
            from app.models.system_logs_model import SystemLog
            SystemLog.log_archive_events(archived_count, True, f"Zarchiwizowano {archived_count} wydarzeń")
            
            return True, f"Zarchiwizowano {archived_count} zakończonych wydarzeń"
                
        except Exception as e:
            from app.models.system_logs_model import SystemLog
            SystemLog.log_archive_events(0, False, f"Błąd archiwizacji: {str(e)}")
            return False, f"Błąd archiwizacji wydarzeń: {str(e)}"