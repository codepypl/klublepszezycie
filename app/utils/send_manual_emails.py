#!/usr/bin/env python3
"""
Skrypt do ręcznego wysyłania emaili do określonych użytkowników
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import create_app, db
from app.models.email_model import EmailTemplate
from app.models.events_model import EventSchedule
from app.models.user_model import User
from app.services.mailgun_service import EnhancedNotificationProcessor

def send_manual_emails(template_id, user_ids, event_id=None):
    """
    Wysyła emaile do określonych użytkowników
    
    Args:
        template_id (int): ID szablonu emaila
        user_ids (list): Lista ID użytkowników
        event_id (int, optional): ID wydarzenia (dla kontekstu)
    """
    app = create_app()
    
    with app.app_context():
        print(f'📧 Wysyłam emaile z szablonu {template_id} do {len(user_ids)} użytkowników...')
        
        # Sprawdź szablon
        template = EmailTemplate.query.get(template_id)
        if not template:
            print(f'❌ Szablon {template_id} nie znaleziony')
            return False
        
        print(f'✅ Szablon: {template.name} - {template.subject}')
        
        # Przygotuj dane kontekstowe
        context = {}
        if event_id:
            event = EventSchedule.query.get(event_id)
            if event:
                context = {
                    'event_id': event.id,
                    'event_title': event.title,
                    'event_date': event.event_date.strftime('%Y-%m-%d'),
                    'event_time': event.event_date.strftime('%H:%M'),
                    'event_location': event.location or 'Online',
                    'event_url': event.meeting_link or '#'
                }
                print(f'✅ Kontekst wydarzenia: {event.title}')
        
        # Pobierz użytkowników
        users = User.query.filter(User.id.in_(user_ids)).all()
        print(f'👥 Znaleziono {len(users)} użytkowników')
        
        if len(users) != len(user_ids):
            found_ids = [user.id for user in users]
            missing_ids = set(user_ids) - set(found_ids)
            print(f'⚠️  Nie znaleziono użytkowników o ID: {missing_ids}')
        
        # Wyślij emaile
        email_processor = EnhancedNotificationProcessor()
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                if not user.email:
                    print(f'⚠️  Użytkownik {user.id} nie ma adresu email')
                    failed_count += 1
                    continue
                
                # Dodaj dane użytkownika do kontekstu
                user_context = context.copy()
                user_context['user_name'] = user.first_name or user.email
                
                # Wyślij email
                success, message = email_processor.send_template_email(
                    to_email=user.email,
                    template_name=template.name,
                    context=user_context,
                    to_name=user.first_name,
                    use_queue=True
                )
                
                if success:
                    sent_count += 1
                    print(f'✅ Wysłano do {user.email} (ID: {user.id})')
                else:
                    failed_count += 1
                    print(f'❌ Błąd wysyłania do {user.email} (ID: {user.id}): {message}')
                    
            except Exception as e:
                failed_count += 1
                print(f'❌ Błąd wysyłania do {user.email} (ID: {user.id}): {str(e)}')
        
        print(f'\\n📊 Podsumowanie:')
        print(f'  ✅ Wysłano: {sent_count}')
        print(f'  ❌ Błędy: {failed_count}')
        print(f'  👥 Razem: {len(users)}')
        
        return sent_count > 0

def main():
    """Główna funkcja"""
    if len(sys.argv) < 3:
        print('Użycie: python send_manual_emails.py <template_id> <user_id1> [user_id2] ... [event_id]')
        print('Przykład: python send_manual_emails.py 502 1 2 3 4 61')
        print('Przykład: python send_manual_emails.py 502 1,2,3,4 61')
        sys.exit(1)
    
    try:
        template_id = int(sys.argv[1])
        
        # Parsuj ID użytkowników
        user_ids_str = sys.argv[2]
        if ',' in user_ids_str:
            user_ids = [int(x.strip()) for x in user_ids_str.split(',')]
        else:
            user_ids = [int(x) for x in sys.argv[2:]]
        
        # Sprawdź czy ostatni argument to event_id
        event_id = None
        if len(sys.argv) > 3:
            try:
                event_id = int(sys.argv[-1])
                user_ids = user_ids[:-1]  # Usuń event_id z listy user_ids
            except ValueError:
                pass  # Ostatni argument nie jest liczbą, więc to nie event_id
        
        print(f'📧 Szablon ID: {template_id}')
        print(f'👥 Użytkownicy ID: {user_ids}')
        if event_id:
            print(f'🎯 Wydarzenie ID: {event_id}')
        
        send_manual_emails(template_id, user_ids, event_id)
        
    except ValueError as e:
        print(f'❌ Błąd: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Błąd: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
