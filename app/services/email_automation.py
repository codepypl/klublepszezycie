"""
Email Automation - automatyzacje emailowe
"""
from datetime import datetime, timedelta
from app.models import db, User, EventSchedule, UserGroup, UserGroupMember
from app.services.email_service import EmailService
from app.services.group_manager import GroupManager
from app.utils.timezone_utils import get_local_now

class EmailAutomation:
    """Automatyzacje emailowe"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.group_manager = GroupManager()
    
    def on_user_registration(self, user_id):
        """Wywoływane przy rejestracji użytkownika"""
        try:
            # Wyślij email powitalny
            user = User.query.get(user_id)
            if user:
                # Generate unsubscribe and delete account URLs
                from app.blueprints.public_controller import generate_unsubscribe_token
                import os
                
                unsubscribe_token = generate_unsubscribe_token(user.email, 'unsubscribe')
                delete_token = generate_unsubscribe_token(user.email, 'delete_account')
                
                # Get base URL from environment or use default
                base_url = os.getenv('BASE_URL', 'https://klublepszezycie.pl')
                
                context = {
                    'user_name': user.first_name or 'Użytkowniku',
                    'user_email': user.email,
                    'temporary_password': 'Sprawdź poprzedni email',  # Password was sent in previous email
                    'login_url': f'{base_url}/login',
                    'unsubscribe_url': f'{base_url}/api/unsubscribe/{user.email}/{unsubscribe_token}',
                    'delete_account_url': f'{base_url}/api/delete-account/{user.email}/{delete_token}'
                }
                
                self.email_service.send_template_email(
                    to_email=user.email,
                    template_name='welcome',
                    context=context,
                    to_name=user.first_name
                )
            
            return True, "Email powitalny wysłany"
            
        except Exception as e:
            return False, f"Błąd wysyłania emaila powitalnego: {str(e)}"
    
    def on_event_registration(self, user_id):
        """Wywoływane przy rejestracji na wydarzenie"""
        try:
            user = User.query.get(user_id)
            if not user or user.account_type != 'event_registration':
                return False, "Użytkownik nie został znaleziony lub nie jest zarejestrowany na wydarzenie"
            
            # Dodaj do grupy wydarzenia (jeśli użytkownik ma konto)
            # Note: user_id field no longer exists in event_registrations table
            # This functionality would need to be reimplemented if needed
            
            # Email potwierdzenia jest już wysyłany w register_event()
            # Ta funkcja może być używana do dodatkowych akcji w przyszłości
            
            return True, "Automatyzacja rejestracji na wydarzenie wykonana"
            
        except Exception as e:
            return False, f"Błąd automatyzacji rejestracji: {str(e)}"
    
    def on_user_joined_club(self, user_id):
        """Wywoływane przy dołączeniu do klubu"""
        try:
            # Dodaj do grupy wszystkich użytkowników (jeśli jeszcze nie jest)
            self.group_manager.add_user_to_all_users(user_id)
            
            # Dodaj do grupy członków
            self.group_manager.add_user_to_club_members(user_id)
            
            # Wyślij email powitalny dla członka
            user = User.query.get(user_id)
            if user:
                # Generate unsubscribe and delete account URLs
                from app.blueprints.public_controller import generate_unsubscribe_token
                import os
                
                unsubscribe_token = generate_unsubscribe_token(user.email, 'unsubscribe')
                delete_token = generate_unsubscribe_token(user.email, 'delete_account')
                
                # Get base URL from environment or use default
                base_url = os.getenv('BASE_URL', 'https://klublepszezycie.pl')
                
                context = {
                    'user_name': user.first_name or 'Użytkowniku',
                    'user_email': user.email,
                    'temporary_password': 'Brak hasła tymczasowego',  # No temp password for existing users
                    'login_url': f'{base_url}/login',
                    'unsubscribe_url': f'{base_url}/api/unsubscribe/{user.email}/{unsubscribe_token}',
                    'delete_account_url': f'{base_url}/api/delete-account/{user.email}/{delete_token}'
                }
                
                self.email_service.send_template_email(
                    to_email=user.email,
                    template_name='welcome',  # Use welcome template instead
                    context=context,
                    to_name=user.first_name
                )
            
            return True, "Użytkownik dodany do klubu"
            
        except Exception as e:
            return False, f"Błąd dodawania do klubu: {str(e)}"
    
    def schedule_event_reminders(self, event_id):
        """Planuje przypomnienia o wydarzeniu"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie zostało znalezione"
            
            # Znajdź grupę wydarzenia
            group = UserGroup.query.filter_by(
                name=f"Wydarzenie: {event.title}",
                group_type='event_based'
            ).first()
            
            if not group:
                return False, "Grupa wydarzenia nie została znaleziona"
            
            # Pobierz członków grupy
            members = UserGroupMember.query.filter_by(group_id=group.id, is_active=True).all()
            
            if not members:
                return False, "Grupa nie ma członków"
            
            # Zaplanuj przypomnienia
            reminders_scheduled = 0
            
            # Convert event date to timezone-aware for comparison
            if event.event_date.tzinfo is None:
                from app.utils.timezone_utils import convert_to_local
                event_date_aware = convert_to_local(event.event_date)
            else:
                event_date_aware = event.event_date
            
            now = get_local_now()
            
            for member in members:
                # Generate unsubscribe and delete account URLs
                from app.blueprints.public_controller import generate_unsubscribe_token
                import os
                
                unsubscribe_token = generate_unsubscribe_token(member.email, 'unsubscribe')
                delete_token = generate_unsubscribe_token(member.email, 'delete_account')
                
                # Get base URL from environment or use default
                base_url = os.getenv('BASE_URL', 'https://klublepszezycie.pl')
                
                context = {
                    'user_name': member.name or 'Użytkowniku',
                    'event_title': event.title,
                    'event_date': event.event_date.strftime('%d.%m.%Y'),
                    'event_time': event.event_date.strftime('%H:%M'),
                    'event_location': event.location or 'Online',
                    'unsubscribe_url': f'{base_url}/api/unsubscribe/{member.email}/{unsubscribe_token}',
                    'delete_account_url': f'{base_url}/api/delete-account/{member.email}/{delete_token}'
                }
                
                # 24h przed
                reminder_24h = event_date_aware - timedelta(hours=24)
                if reminder_24h > now:
                    # Użyj szablonu zamiast generować HTML
                    success, message = self.email_service.send_template_email(
                        to_email=member.email,
                        template_name='event_reminder_24h',
                        context=context,
                        to_name=member.name
                    )
                    if success:
                        reminders_scheduled += 1
                
                # 1h przed
                reminder_1h = event_date_aware - timedelta(hours=1)
                if reminder_1h > now:
                    # Użyj szablonu zamiast generować HTML
                    success, message = self.email_service.send_template_email(
                        to_email=member.email,
                        template_name='event_reminder_1h',
                        context=context,
                        to_name=member.name
                    )
                    if success:
                        reminders_scheduled += 1
                
                # 5min przed
                reminder_5min = event_date_aware - timedelta(minutes=5)
                if reminder_5min > now:
                    # Dodaj meeting_link do kontekstu
                    context_with_link = context.copy()
                    context_with_link['meeting_link'] = event.meeting_link or ''
                    
                    # Użyj szablonu zamiast generować HTML
                    success, message = self.email_service.send_template_email(
                        to_email=member.email,
                        template_name='event_reminder_5min',
                        context=context_with_link,
                        to_name=member.name
                    )
                    if success:
                        reminders_scheduled += 1
            
            return True, f"Zaplanowano {reminders_scheduled} przypomnień"
            
        except Exception as e:
            return False, f"Błąd planowania przypomnień: {str(e)}"
    
    def process_event_reminders(self):
        """Przetwarza przypomnienia o wydarzeniach (wywoływane przez cron)"""
        try:
            # Znajdź wydarzenia w najbliższych 25 godzinach
            now = get_local_now()
            future_events = EventSchedule.query.filter(
                EventSchedule.event_date > now,
                EventSchedule.event_date <= now + timedelta(hours=25)
            ).all()
            
            processed = 0
            
            for event in future_events:
                # Sprawdź czy przypomnienia już zostały zaplanowane
                group = UserGroup.query.filter_by(
                    name=f"Wydarzenie: {event.title}",
                    group_type='event_based'
                ).first()
                
                if group and group.member_count > 0:
                    # Zaplanuj przypomnienia
                    success, message = self.schedule_event_reminders(event.id)
                    if success:
                        processed += 1
            
            return True, f"Przetworzono {processed} wydarzeń"
            
        except Exception as e:
            return False, f"Błąd przetwarzania przypomnień: {str(e)}"
    
    def send_admin_notification(self, event_id, user_id):
        """Wysyła powiadomienie do administratorów o nowej rejestracji"""
        try:
            user = User.query.get(user_id)
            event = EventSchedule.query.get(event_id)
            
            if not user or not event:
                return False, "Użytkownik lub wydarzenie nie zostało znalezione"
            
            # Znajdź administratorów
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            
            if not admins:
                return False, "Brak aktywnych administratorów"
            
            # Wyślij powiadomienie do każdego administratora
            sent = 0
            for admin in admins:
                context = {
                    'admin_name': admin.name or 'Administratorze',
                    'user_name': registration.first_name,
                    'user_email': registration.email,
                    'event_title': event.title,
                    'event_date': event.event_date.strftime('%d.%m.%Y %H:%M')
                }
                
                success, message = self.email_service.send_template_email(
                    to_email=admin.email,
                    template_name='admin_notification',
                    context=context,
                    to_name=admin.name
                )
                
                if success:
                    sent += 1
            
            return True, f"Powiadomienia wysłane do {sent} administratorów"
            
        except Exception as e:
            return False, f"Błąd wysyłania powiadomień: {str(e)}"
    
    def update_all_groups(self):
        """Aktualizuje wszystkie grupy na podstawie aktualnych danych"""
        try:
            groups = UserGroup.query.filter_by(is_active=True).all()
            updated = 0
            
            for group in groups:
                success, message = self.group_manager.update_group_members(group.id)
                if success:
                    updated += 1
            
            return True, f"Zaktualizowano {updated} grup"
            
        except Exception as e:
            return False, f"Błąd aktualizacji grup: {str(e)}"
    
    def archive_ended_events(self):
        """Archiwizuje wydarzenia, które się zakończyły"""
        try:
            # Znajdź wydarzenia, które się zakończyły ale nie są jeszcze zarchiwizowane
            events = EventSchedule.query.filter(
                EventSchedule.is_archived == False
            ).all()
            
            archived_count = 0
            
            for event in events:
                if event.is_ended():
                    event.archive()
                    archived_count += 1
                    print(f"Archiwizowano wydarzenie: {event.title} ({event.event_date})")
            
            if archived_count > 0:
                db.session.commit()
                return True, f"Zarchiwizowano {archived_count} wydarzeń"
            else:
                return True, "Brak wydarzeń do zarchiwizowania"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Błąd archiwizowania wydarzeń: {str(e)}"


