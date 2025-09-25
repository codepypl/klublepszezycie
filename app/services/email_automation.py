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
        self.email_processor = EnhancedNotificationProcessor()
    
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
            
            # Znajdź odpowiednią grupę
            if group_type == 'event_based':
                group = UserGroup.query.filter_by(
                    name=f"Wydarzenie: {event.title}",
                    group_type='event_based'
                ).first()
                group_name = "wydarzenia"
            elif group_type == 'club_members':
                group = UserGroup.query.filter_by(
                    name="Członkowie klubu",
                    group_type='club_members'
                ).first()
                group_name = "klubu"
            else:
                return False, "Nieprawidłowy typ grupy"
            
            if not group:
                return False, f"Grupa {group_name} nie została znaleziona"
            
            # Pobierz członków grupy
            members = UserGroupMember.query.filter_by(group_id=group.id, is_active=True).all()
            
            if not members:
                return False, "Grupa nie ma członków"
            
            # Użyj inteligentnego planowania
            return self.schedule_event_reminders_smart(event_id, group_type, len(members))
            
        except Exception as e:
            return False, f"Błąd planowania przypomnień: {str(e)}"
    
    def schedule_event_reminders_smart(self, event_id, group_type='event_based', participants_count=None):
        """Planuje przypomnienia o wydarzeniu z inteligentnym planowaniem czasu"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie zostało znalezione"
            
            # Znajdź odpowiednią grupę
            if group_type == 'event_based':
                group = UserGroup.query.filter_by(
                    name=f"Wydarzenie: {event.title}",
                    group_type='event_based'
                ).first()
                group_name = "wydarzenia"
            elif group_type == 'club_members':
                group = UserGroup.query.filter_by(
                    name="Członkowie klubu",
                    group_type='club_members'
                ).first()
                group_name = "klubu"
            else:
                return False, "Nieprawidłowy typ grupy"
            
            if not group:
                return False, f"Grupa {group_name} nie została znaleziona"
            
            # Pobierz członków grupy
            members = UserGroupMember.query.filter_by(group_id=group.id, is_active=True).all()
            
            if not members:
                return False, "Grupa nie ma członków"
            
            # Użyj podanej liczby uczestników lub policz
            if participants_count is None:
                participants_count = len(members)
            
            # Zaplanuj przypomnienia z inteligentnym planowaniem
            reminders_scheduled = 0
            
            # Convert event date to timezone-aware for comparison
            if event.event_date.tzinfo is None:
                from app.utils.timezone_utils import convert_to_local
                event_date_aware = convert_to_local(event.event_date)
            else:
                event_date_aware = event.event_date
            
            now = get_local_now()
            
            # Inteligentne planowanie - oblicz optymalny czas wysyłki
            from app.services.email_service import EmailService
            email_service = EmailService()
            
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
                
                # Sprawdź czy nie jest za późno
                if optimal_send_time < now:
                    print(f"⚠️ Za późno na przypomnienie {schedule['type']} przed wydarzeniem")
                    continue
                
                print(f"📅 Zaplanowano przypomnienie {schedule['type']}: {optimal_send_time} (docelowo: {target_time})")
                
                # Zaplanuj wysyłkę przez Celery (tymczasowo wyłączone)
                try:
                    from app.tasks.email_tasks import schedule_event_reminders_task
                    schedule_event_reminders_task.apply_async(
                        args=[event_id, group_type],
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
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
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