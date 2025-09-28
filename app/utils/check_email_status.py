#!/usr/bin/env python3
"""
Skrypt do sprawdzania statusu emaili na podstawie ID szablonu i ID wydarzenia
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import create_app, db
from app.models.email_model import EmailLog, EmailTemplate, EmailQueue
from app.models.events_model import EventSchedule
from app.models.user_model import User
from app.models.email_model import UserGroup, UserGroupMember

def check_email_status(template_id, event_id):
    """
    Sprawdza kto otrzymał email z danego szablonu dla danego wydarzenia
    
    Args:
        template_id (int): ID szablonu emaila
        event_id (int): ID wydarzenia
    """
    app = create_app()
    
    with app.app_context():
        print(f'🔍 Sprawdzam status emaili dla szablonu {template_id} i wydarzenia {event_id}...')
        
        # Sprawdź szablon
        template = EmailTemplate.query.get(template_id)
        if not template:
            print(f'❌ Szablon {template_id} nie znaleziony')
            return
        
        print(f'✅ Szablon: {template.name} - {template.subject}')
        
        # Sprawdź wydarzenie
        event = EventSchedule.query.get(event_id)
        if not event:
            print(f'❌ Wydarzenie {event_id} nie znalezione')
            return
        
        print(f'✅ Wydarzenie: {event.title} ({event.event_date})')
        
        # Pobierz wszystkich członków klubu
        club_group = UserGroup.query.filter_by(
            name='Członkowie klubu',
            group_type='club_members'
        ).first()
        
        if not club_group:
            print('❌ Grupa klubu nie znaleziona')
            return
        
        club_members = UserGroupMember.query.filter_by(
            group_id=club_group.id,
            is_active=True
        ).all()
        
        print(f'👥 {len(club_members)} aktywnych członków klubu')
        
        # Pobierz listę osób które otrzymały email
        sent_emails = EmailLog.query.filter(
            EmailLog.template_id == template_id,
            EmailLog.status == 'sent'
        ).all()
        
        received_emails = set()
        for email_log in sent_emails:
            received_emails.add(email_log.email)
        
        print(f'📧 {len(received_emails)} osób otrzymało email')
        
        # Sprawdź kto nie otrzymał
        members_without_email = []
        members_with_email = []
        
        for member in club_members:
            user = User.query.get(member.user_id)
            if user and user.email:
                if user.email in received_emails:
                    members_with_email.append(user)
                else:
                    members_without_email.append(user)
        
        print(f'\\n📊 Podsumowanie:')
        print(f'  ✅ Otrzymało email: {len(members_with_email)}')
        print(f'  ❌ Nie otrzymało: {len(members_without_email)}')
        print(f'  👥 Razem członków: {len(club_members)}')
        
        if members_with_email:
            print(f'\\n✅ Osoby które otrzymały email:')
            for user in members_with_email:
                print(f'  - ID: {user.id}, Email: {user.email}, Imię: {user.first_name or \"Brak\"}')
        
        if members_without_email:
            print(f'\\n❌ Osoby które NIE otrzymały email:')
            for user in members_without_email:
                print(f'  - ID: {user.id}, Email: {user.email}, Imię: {user.first_name or \"Brak\"}')
        
        # Sprawdź kolejkę emaili
        print(f'\\n📬 Sprawdzam kolejkę emaili...')
        queue_emails = EmailQueue.query.filter(
            EmailQueue.template_id == template_id,
            EmailQueue.status == 'pending'
        ).all()
        
        print(f'📧 {len(queue_emails)} emaili w kolejce')
        
        if queue_emails:
            print('📋 Emaile w kolejce:')
            for email in queue_emails:
                print(f'  - {email.recipient_email} (zaplanowany: {email.scheduled_at})')

def main():
    """Główna funkcja"""
    if len(sys.argv) != 3:
        print('Użycie: python check_email_status.py <template_id> <event_id>')
        print('Przykład: python check_email_status.py 502 61')
        sys.exit(1)
    
    try:
        template_id = int(sys.argv[1])
        event_id = int(sys.argv[2])
        check_email_status(template_id, event_id)
    except ValueError:
        print('❌ Błąd: ID musi być liczbą')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Błąd: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
