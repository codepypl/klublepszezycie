#!/usr/bin/env python3
"""
Skrypt do resetowania systemu emaili w Klubie Lepsze Życie
Usuwa wszystkie harmonogramy i szablony emaili, a następnie tworzy je na nowo
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import (
    EmailTemplate, EmailSchedule, EventEmailSchedule, 
    EmailAutomation, EmailCampaign, EmailLog,
    EventSchedule
)

def reset_email_system():
    """Reset całego systemu emaili"""
    
    with app.app_context():
        try:
            print("🔄 Rozpoczynam reset systemu emaili...")
            print("=" * 50)
            
            # 1. Usuń wszystkie harmonogramy emaili dla wydarzeń
            print("1. Usuwanie harmonogramów emaili dla wydarzeń...")
            event_schedules = EventEmailSchedule.query.all()
            for schedule in event_schedules:
                db.session.delete(schedule)
            print(f"   ✅ Usunięto {len(event_schedules)} harmonogramów wydarzeń")
            
            # 2. Usuń wszystkie harmonogramy emaili (EmailSchedule) PRZED usunięciem szablonów
            print("2. Usuwanie harmonogramów emaili...")
            schedules = EmailSchedule.query.all()
            for schedule in schedules:
                db.session.delete(schedule)
            print(f"   ✅ Usunięto {len(schedules)} harmonogramów emaili")
            
            # 3. Usuń wszystkie szablony emaili
            print("3. Usuwanie szablonów emaili...")
            templates = EmailTemplate.query.all()
            for template in templates:
                db.session.delete(template)
            print(f"   ✅ Usunięto {len(templates)} szablonów emaili")
            
            # 4. Usuń wszystkie automatyzacje emaili
            print("4. Usuwanie automatyzacji emaili...")
            automations = EmailAutomation.query.all()
            for automation in automations:
                db.session.delete(automation)
            print(f"   ✅ Usunięto {len(automations)} automatyzacji emaili")
            
            # 5. Usuń wszystkie kampanie emaili
            print("5. Usuwanie kampanii emaili...")
            campaigns = EmailCampaign.query.all()
            for campaign in campaigns:
                db.session.delete(campaign)
            print(f"   ✅ Usunięto {len(campaigns)} kampanii emaili")
            
            # 6. Usuń wszystkie logi emaili
            print("6. Usuwanie logów emaili...")
            logs = EmailLog.query.all()
            for log in logs:
                db.session.delete(log)
            print(f"   ✅ Usunięto {len(logs)} logów emaili")
            
            # Zatwierdź wszystkie usunięcia
            db.session.commit()
            print("\n🧹 Wszystkie dane emaili zostały usunięte!")
            print("=" * 50)
            
            # 7. Utwórz domyślne szablony emaili
            print("7. Tworzenie domyślnych szablonów emaili...")
            created_templates = create_default_templates()
            print(f"   ✅ Utworzono {len(created_templates)} szablonów emaili")
            
            # 8. Utwórz harmonogramy emaili dla istniejących wydarzeń
            print("8. Tworzenie harmonogramów dla istniejących wydarzeń...")
            events = EventSchedule.query.all()
            total_schedules = 0
            
            for event in events:
                try:
                    # Utwórz harmonogramy bezpośrednio, niezależnie od daty
                    schedules = create_event_schedules(event.id)
                    total_schedules += len(schedules)
                    print(f"   📅 Wydarzenie '{event.title}': {len(schedules)} harmonogramów")
                except Exception as e:
                    print(f"   ❌ Błąd dla wydarzenia '{event.title}': {e}")
            
            print(f"   ✅ Utworzono łącznie {total_schedules} harmonogramów wydarzeń")
            
            # 9. Utwórz domyślne harmonogramy EmailSchedule
            print("9. Tworzenie domyślnych harmonogramów EmailSchedule...")
            created_schedules = create_default_schedules()
            print(f"   ✅ Utworzono {len(created_schedules)} harmonogramów EmailSchedule")
            
            print("\n🎉 Reset systemu emaili zakończony pomyślnie!")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Błąd podczas resetu systemu emaili: {e}")
            db.session.rollback()
            return False

def create_default_templates():
    """Tworzy domyślne szablony emaili"""
    
    templates = []
    
    # Lista szablonów do utworzenia
    template_configs = [
        {
            'template_type': 'welcome',
            'name': 'Email Powitalny',
            'subject': 'Witamy w Klubie Lepsze Życie! 🎉',
            'html_content': '<h1>Witamy w Klubie Lepsze Życie!</h1><p>Cześć {{name}}! Dziękujemy za dołączenie.</p>',
            'text_content': 'Witamy w Klubie Lepsze Życie!\n\nCześć {{name}}! Dziękujemy za dołączenie.',
            'variables': 'name,email'
        },
        {
            'template_type': 'user_activation',
            'name': 'Aktywacja Konta',
            'subject': 'Witamy w Klubie Lepsze Życie! 🎉 - Twoje hasło',
            'html_content': '<h1>Witamy w Klubie Lepsze Życie!</h1><p>Cześć {{name}}! Twoje konto zostało utworzone.</p><p><strong>Twoje tymczasowe hasło:</strong> {{temporary_password}}</p><p>Zaloguj się i zmień hasło w swoim profilu.</p>',
            'text_content': 'Witamy w Klubie Lepsze Życie!\n\nCześć {{name}}! Twoje konto zostało utworzone.\n\nTwoje tymczasowe hasło: {{temporary_password}}\n\nZaloguj się i zmień hasło w swoim profilu.',
            'variables': 'name,email,temporary_password'
        },
        {
            'template_type': 'admin_notification',
            'name': 'Nowa osoba dołączyła do klubu',
            'subject': '🔔 Nowa rejestracja: {{name}}',
            'html_content': '<h1>Nowa Rejestracja</h1><p>Nowa osoba dołączyła do klubu: {{name}} ({{email}})</p>',
            'text_content': 'Nowa Rejestracja\n\nNowa osoba dołączyła do klubu: {{name}} ({{email}})',
            'variables': 'name,email'
        },
        {
            'template_type': 'event_reminder_24h_before',
            'name': 'event_reminder_24h_before',
            'subject': '🔔 Przypomnienie: {{event_title}} - jutro o {{event_time}}',
            'html_content': '<h1>Przypomnienie 24h przed wydarzeniem</h1><p>Cześć {{name}}! Jutro o {{event_time}} odbędzie się {{event_title}}.</p>',
            'text_content': 'Przypomnienie 24h przed wydarzeniem\n\nCześć {{name}}! Jutro o {{event_time}} odbędzie się {{event_title}}.',
            'variables': 'name,email,event_title,event_time'
        },
        {
            'template_type': 'event_reminder_1h_before',
            'name': 'event_reminder_1h_before',
            'subject': '🔔 Przypomnienie: {{event_title}} - za godzinę!',
            'html_content': '<h1>Przypomnienie 1h przed wydarzeniem</h1><p>Cześć {{name}}! Za godzinę odbędzie się {{event_title}}.</p>',
            'text_content': 'Przypomnienie 1h przed wydarzeniem\n\nCześć {{name}}! Za godzinę odbędzie się {{event_title}}.',
            'variables': 'name,email,event_title'
        },
        {
            'template_type': 'event_reminder_5min_before',
            'name': 'event_reminder_5min_before',
            'subject': '🔗 Link do spotkania: {{event_title}} - za 5 minut!',
            'html_content': '<h1>Link do spotkania</h1><p>Cześć {{name}}! Za 5 minut rozpocznie się {{event_title}}. Link: {{event_meeting_link}}</p>',
            'text_content': 'Link do spotkania\n\nCześć {{name}}! Za 5 minut rozpocznie się {{event_title}}. Link: {{event_meeting_link}}',
            'variables': 'name,email,event_title,event_meeting_link'
        },
        {
            'template_type': 'event_registration',
            'name': 'event_registration_confirmation',
            'subject': '✅ Potwierdzenie zapisu na wydarzenie: {{event_title}}',
            'html_content': '<h1>Potwierdzenie zapisu</h1><p>Cześć {{name}}! Twoje miejsce na wydarzenie {{event_title}} zostało zarezerwowane.</p>',
            'text_content': 'Potwierdzenie zapisu\n\nCześć {{name}}! Twoje miejsce na wydarzenie {{event_title}} zostało zarezerwowane.',
            'variables': 'name,email,event_title'
        }
    ]
    
    # Utwórz szablony
    for config in template_configs:
        # Sprawdź, czy szablon już istnieje
        existing_template = EmailTemplate.query.filter_by(template_type=config['template_type']).first()
        if not existing_template:
            template = EmailTemplate(
                name=config['name'],
                subject=config['subject'],
                html_content=config['html_content'],
                text_content=config['text_content'],
                template_type=config['template_type'],
                variables=config['variables'],
                is_active=True
            )
            db.session.add(template)
            templates.append(config['template_type'])
    
    # Zatwierdź wszystkie szablony
    db.session.commit()
    
    return templates

def create_default_schedules():
    """Tworzy domyślne harmonogramy EmailSchedule"""
    schedules = []
    
    # Konfiguracja harmonogramów
    schedule_configs = [
        {
            'name': 'Email Powitalny',
            'description': 'Automatyczny email powitalny wysyłany gdy konto użytkownika zostanie utworzone',
            'template_type': 'user_activation',
            'trigger_type': 'user_activation',
            'trigger_conditions': '{"event": "user_activation"}',
            'recipient_type': 'user',
            'send_type': 'immediate',
            'status': 'active'
        },
        {
            'name': 'Potwierdzenie Zapisu na Wydarzenie',
            'description': 'Automatyczny email potwierdzający zapis na wydarzenie',
            'template_type': 'event_registration',
            'trigger_type': 'event_registration',
            'trigger_conditions': '{"event": "event_registration"}',
            'recipient_type': 'user',
            'send_type': 'immediate',
            'status': 'active'
        },
        {
            'name': 'Powiadomienie Admina o Nowej Rejestracji',
            'description': 'Powiadomienie administratora o nowej rejestracji w klubie',
            'template_type': 'admin_notification',
            'trigger_type': 'admin_notification',
            'trigger_conditions': '{"event": "admin_notification"}',
            'recipient_type': 'admin',
            'send_type': 'immediate',
            'status': 'active'
        },
        {
            'name': 'Przypomnienie 24h przed wydarzeniem',
            'description': 'Automatyczne przypomnienie 24 godzin przed wydarzeniem',
            'template_type': 'event_reminder_24h_before',
            'trigger_type': 'event_reminder',
            'trigger_conditions': '{"event": "event_reminder", "type": "24h_before"}',
            'recipient_type': 'event_registrations',
            'send_type': 'scheduled',
            'status': 'active'
        },
        {
            'name': 'Przypomnienie 1h przed wydarzeniem',
            'description': 'Automatyczne przypomnienie 1 godzinę przed wydarzeniem',
            'template_type': 'event_reminder_1h_before',
            'trigger_type': 'event_reminder',
            'trigger_conditions': '{"event": "event_reminder", "type": "1h_before"}',
            'recipient_type': 'event_registrations',
            'send_type': 'scheduled',
            'status': 'active'
        },
        {
            'name': 'Link do spotkania 5min przed wydarzeniem',
            'description': 'Automatyczne wysłanie linku do spotkania 5 minut przed wydarzeniem',
            'template_type': 'event_reminder_5min_before',
            'trigger_type': 'event_reminder',
            'trigger_conditions': '{"event": "event_reminder", "type": "5min_before"}',
            'recipient_type': 'event_registrations',
            'send_type': 'scheduled',
            'status': 'active'
        }
    ]
    
    # Utwórz harmonogramy
    for config in schedule_configs:
        # Sprawdź, czy harmonogram już istnieje
        existing_schedule = EmailSchedule.query.filter_by(name=config['name']).first()
        if not existing_schedule:
            # Znajdź odpowiedni szablon
            template = EmailTemplate.query.filter_by(template_type=config['template_type']).first()
            if template:
                schedule = EmailSchedule(
                    name=config['name'],
                    description=config['description'],
                    template_id=template.id,
                    trigger_type=config['trigger_type'],
                    trigger_conditions=config['trigger_conditions'],
                    recipient_type=config['recipient_type'],
                    send_type=config['send_type'],
                    status=config['status']
                )
                db.session.add(schedule)
                schedules.append(config['name'])
    
    # Zatwierdź wszystkie harmonogramy
    db.session.commit()
    
    return schedules

def create_event_schedules(event_id):
    """Tworzy harmonogramy EventEmailSchedule dla wydarzenia, niezależnie od daty"""
    from models import EventEmailSchedule, EventSchedule
    from datetime import timedelta
    
    schedules = []
    
    # Pobierz wydarzenie
    event = EventSchedule.query.get(event_id)
    if not event:
        return schedules
    
    # Typy przypomnień
    reminder_types = [
        ('24h_before', timedelta(hours=24)),
        ('1h_before', timedelta(hours=1)),
        ('5min_before', timedelta(minutes=5))
    ]
    
    for reminder_type, time_offset in reminder_types:
        # Sprawdź, czy harmonogram już istnieje
        existing_schedule = EventEmailSchedule.query.filter_by(
            event_id=event_id,
            notification_type=reminder_type
        ).first()
        
        if existing_schedule:
            continue
        
        # Znajdź szablon
        template_name = f'event_reminder_{reminder_type}'
        template = EmailTemplate.query.filter_by(template_type=template_name).first()
        
        if template:
            # Oblicz zaplanowany czas (nawet jeśli w przeszłości)
            scheduled_time = event.event_date - time_offset
            
            schedule = EventEmailSchedule(
                event_id=event_id,
                notification_type=reminder_type,
                scheduled_at=scheduled_time,
                template_id=template.id,
                status='pending'
            )
            
            db.session.add(schedule)
            schedules.append(schedule)
    
    # Zatwierdź harmonogramy
    db.session.commit()
    
    return schedules

if __name__ == "__main__":
    print("🚀 Uruchamianie skryptu resetu systemu emaili...")
    print("⚠️  UWAGA: Ten skrypt usunie WSZYSTKIE dane emaili z systemu!")
    
    # Potwierdzenie
    response = input("\nCzy na pewno chcesz kontynuować? (tak/nie): ").lower().strip()
    
    if response in ['tak', 'yes', 'y', 't']:
        success = reset_email_system()
        
        if success:
            print("\n🎉 Reset systemu emaili zakończony pomyślnie!")
            print("✅ Wszystkie harmonogramy i szablony zostały odtworzone")
        else:
            print("\n❌ Reset systemu emaili nie powiódł się!")
            sys.exit(1)
    else:
        print("\n❌ Anulowano reset systemu emaili")
        sys.exit(0)