"""
Skrypt do ręcznego testowania Email Schedulera v3

Testuje różne scenariusze:
1. Wydarzenie za 24h+ (powinno zaplanować 3 przypomnienia)
2. Wydarzenie za 1h+ (powinno zaplanować 2 przypomnienia)
3. Wydarzenie za 5min+ (powinno zaplanować 1 przypomnienie)
4. Kampania natychmiastowa (priorytet 2, scheduled_at = teraz)
5. Kampania planowana (priorytet 2, scheduled_at = przyszłość)
"""
import sys
import os
from datetime import datetime, timedelta

# Dodaj ścieżkę projektu do sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models import EventSchedule, EmailCampaign, EmailQueue, User, EmailTemplate
from app.services.email_v2.queue.scheduler import EmailScheduler
from app.utils.timezone_utils import get_local_now


def clear_test_data():
    """Czyści dane testowe"""
    print("\n🗑️  Czyszczenie danych testowych...")
    
    # Usuń testowe wydarzenia
    test_events = EventSchedule.query.filter(
        EventSchedule.title.like('TEST:%')
    ).all()
    
    for event in test_events:
        # Usuń emaile powiązane z wydarzeniem
        EmailQueue.query.filter_by(event_id=event.id).delete()
        db.session.delete(event)
    
    # Usuń testowe kampanie
    test_campaigns = EmailCampaign.query.filter(
        EmailCampaign.name.like('TEST:%')
    ).all()
    
    for campaign in test_campaigns:
        # Usuń emaile powiązane z kampanią
        EmailQueue.query.filter_by(campaign_id=campaign.id).delete()
        db.session.delete(campaign)
    
    db.session.commit()
    print("✅ Dane testowe wyczyszczone")


def create_test_user():
    """Tworzy użytkownika testowego"""
    user = User.query.filter_by(email='test.scheduler@example.com').first()
    
    if not user:
        user = User(
            email='test.scheduler@example.com',
            first_name='Test',
            last_name='Scheduler',
            club_member=True,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        print(f"✅ Utworzono użytkownika testowego: {user.email}")
    else:
        print(f"ℹ️  Użytkownik testowy już istnieje: {user.email}")
    
    return user


def test_event_24h_plus():
    """Test: Wydarzenie za 24h+"""
    print("\n" + "="*60)
    print("TEST 1: Wydarzenie za 24h+ (powinno zaplanować 3 przypomnienia)")
    print("="*60)
    
    now = get_local_now()
    event_date = now + timedelta(hours=48)  # Za 48h
    
    # Utwórz wydarzenie testowe
    event = EventSchedule(
        title='TEST: Wydarzenie za 48h',
        event_type='workshop',
        event_date=event_date,
        description='Wydarzenie testowe dla schedulera',
        location='Online',
        is_active=True,
        is_published=True,
        reminders_scheduled=False
    )
    db.session.add(event)
    db.session.commit()
    
    print(f"📅 Utworzono wydarzenie: {event.title} (ID: {event.id})")
    print(f"   Data wydarzenia: {event.event_date}")
    print(f"   Czas do wydarzenia: {event_date - now}")
    
    # Zaplanuj przypomnienia
    scheduler = EmailScheduler()
    success, message = scheduler.schedule_event_reminders(event.id)
    
    print(f"\n{'✅' if success else '❌'} Wynik: {message}")
    
    # Sprawdź kolejkę
    queue_items = EmailQueue.query.filter_by(event_id=event.id).all()
    print(f"\n📊 Emaile w kolejce: {len(queue_items)}")
    
    for item in queue_items:
        print(f"   - {item.template_name} | Priorytet: {item.priority} | Scheduled: {item.scheduled_at}")
    
    return event.id


def test_event_1h_plus():
    """Test: Wydarzenie za 1h+"""
    print("\n" + "="*60)
    print("TEST 2: Wydarzenie za 1h+ (powinno zaplanować 2 przypomnienia)")
    print("="*60)
    
    now = get_local_now()
    event_date = now + timedelta(hours=2)  # Za 2h
    
    # Utwórz wydarzenie testowe
    event = EventSchedule(
        title='TEST: Wydarzenie za 2h',
        event_type='meeting',
        event_date=event_date,
        description='Wydarzenie testowe dla schedulera',
        location='Online',
        is_active=True,
        is_published=True,
        reminders_scheduled=False
    )
    db.session.add(event)
    db.session.commit()
    
    print(f"📅 Utworzono wydarzenie: {event.title} (ID: {event.id})")
    print(f"   Data wydarzenia: {event.event_date}")
    print(f"   Czas do wydarzenia: {event_date - now}")
    
    # Zaplanuj przypomnienia
    scheduler = EmailScheduler()
    success, message = scheduler.schedule_event_reminders(event.id)
    
    print(f"\n{'✅' if success else '❌'} Wynik: {message}")
    
    # Sprawdź kolejkę
    queue_items = EmailQueue.query.filter_by(event_id=event.id).all()
    print(f"\n📊 Emaile w kolejce: {len(queue_items)}")
    
    for item in queue_items:
        print(f"   - {item.template_name} | Priorytet: {item.priority} | Scheduled: {item.scheduled_at}")
    
    return event.id


def test_event_5min_plus():
    """Test: Wydarzenie za 5min+"""
    print("\n" + "="*60)
    print("TEST 3: Wydarzenie za 5min+ (powinno zaplanować 1 przypomnienie)")
    print("="*60)
    
    now = get_local_now()
    event_date = now + timedelta(minutes=10)  # Za 10 minut
    
    # Utwórz wydarzenie testowe
    event = EventSchedule(
        title='TEST: Wydarzenie za 10min',
        event_type='call',
        event_date=event_date,
        description='Wydarzenie testowe dla schedulera',
        location='Online',
        is_active=True,
        is_published=True,
        reminders_scheduled=False
    )
    db.session.add(event)
    db.session.commit()
    
    print(f"📅 Utworzono wydarzenie: {event.title} (ID: {event.id})")
    print(f"   Data wydarzenia: {event.event_date}")
    print(f"   Czas do wydarzenia: {event_date - now}")
    
    # Zaplanuj przypomnienia
    scheduler = EmailScheduler()
    success, message = scheduler.schedule_event_reminders(event.id)
    
    print(f"\n{'✅' if success else '❌'} Wynik: {message}")
    
    # Sprawdź kolejkę
    queue_items = EmailQueue.query.filter_by(event_id=event.id).all()
    print(f"\n📊 Emaile w kolejce: {len(queue_items)}")
    
    for item in queue_items:
        print(f"   - {item.template_name} | Priorytet: {item.priority} | Scheduled: {item.scheduled_at}")
    
    return event.id


def test_priority_queue():
    """Test: Sprawdź priorytetyzację w kolejce"""
    print("\n" + "="*60)
    print("TEST 4: Priorytetyzacja w kolejce")
    print("="*60)
    
    # Pobierz wszystkie emaile z kolejki
    all_emails = EmailQueue.query.filter_by(status='pending').order_by(
        EmailQueue.priority.asc(),
        EmailQueue.scheduled_at.asc()
    ).limit(20).all()
    
    print(f"\n📊 Kolejka emaili (20 pierwszych, sorted by priority):")
    print(f"{'Priorytet':<12} {'Template':<30} {'Scheduled':<20} {'Email':<30}")
    print("-" * 92)
    
    for email in all_emails:
        priority_name = {
            0: 'SYSTEM',
            1: 'EVENT',
            2: 'CAMPAIGN'
        }.get(email.priority, 'UNKNOWN')
        
        template_name = email.template_name or 'N/A'
        scheduled = email.scheduled_at.strftime('%Y-%m-%d %H:%M') if email.scheduled_at else 'N/A'
        recipient = email.recipient_email[:28] + '...' if len(email.recipient_email) > 28 else email.recipient_email
        
        print(f"{priority_name:<12} {template_name:<30} {scheduled:<20} {recipient:<30}")


def test_campaign_immediate():
    """Test: Kampania natychmiastowa"""
    print("\n" + "="*60)
    print("TEST 5: Kampania natychmiastowa (priorytet 2, scheduled_at = teraz)")
    print("="*60)
    
    # Sprawdź czy istnieje szablon
    template = EmailTemplate.query.filter_by(name='default_campaign').first()
    if not template:
        print("⚠️  Brak szablonu 'default_campaign' - pomijam test")
        return None
    
    # Utwórz kampanię testową
    campaign = EmailCampaign(
        name='TEST: Kampania natychmiastowa',
        description='Testowa kampania natychmiastowa',
        subject='Test natychmiastowy',
        html_content='<p>Test</p>',
        text_content='Test',
        template_id=template.id,
        recipient_type='custom',
        custom_emails='["test.scheduler@example.com"]',
        status='draft',
        send_type='immediate'
    )
    db.session.add(campaign)
    db.session.commit()
    
    print(f"📧 Utworzono kampanię: {campaign.name} (ID: {campaign.id})")
    print(f"   Typ wysyłki: {campaign.send_type}")
    
    # Zaplanuj kampanię
    scheduler = EmailScheduler()
    success, message = scheduler.schedule_campaign(campaign.id)
    
    print(f"\n{'✅' if success else '❌'} Wynik: {message}")
    
    # Sprawdź kolejkę
    queue_items = EmailQueue.query.filter_by(campaign_id=campaign.id).all()
    print(f"\n📊 Emaile w kolejce: {len(queue_items)}")
    
    for item in queue_items:
        print(f"   - Priorytet: {item.priority} | Scheduled: {item.scheduled_at}")
    
    return campaign.id


def test_campaign_scheduled():
    """Test: Kampania planowana"""
    print("\n" + "="*60)
    print("TEST 6: Kampania planowana (priorytet 2, scheduled_at = przyszłość)")
    print("="*60)
    
    # Sprawdź czy istnieje szablon
    template = EmailTemplate.query.filter_by(name='default_campaign').first()
    if not template:
        print("⚠️  Brak szablonu 'default_campaign' - pomijam test")
        return None
    
    now = get_local_now()
    scheduled_time = now + timedelta(hours=24)  # Za 24h
    
    # Utwórz kampanię testową
    campaign = EmailCampaign(
        name='TEST: Kampania planowana',
        description='Testowa kampania planowana',
        subject='Test planowany',
        html_content='<p>Test</p>',
        text_content='Test',
        template_id=template.id,
        recipient_type='custom',
        custom_emails='["test.scheduler@example.com"]',
        status='draft',
        send_type='scheduled',
        scheduled_at=scheduled_time
    )
    db.session.add(campaign)
    db.session.commit()
    
    print(f"📧 Utworzono kampanię: {campaign.name} (ID: {campaign.id})")
    print(f"   Typ wysyłki: {campaign.send_type}")
    print(f"   Scheduled at: {campaign.scheduled_at}")
    
    # Zaplanuj kampanię
    scheduler = EmailScheduler()
    success, message = scheduler.schedule_campaign(campaign.id)
    
    print(f"\n{'✅' if success else '❌'} Wynik: {message}")
    
    # Sprawdź kolejkę
    queue_items = EmailQueue.query.filter_by(campaign_id=campaign.id).all()
    print(f"\n📊 Emaile w kolejce: {len(queue_items)}")
    
    for item in queue_items:
        print(f"   - Priorytet: {item.priority} | Scheduled: {item.scheduled_at}")
    
    return campaign.id


def main():
    """Główna funkcja testowa"""
    print("\n" + "="*60)
    print("EMAIL SCHEDULER v3 - MANUAL TESTING")
    print("="*60)
    
    # Utwórz aplikację Flask
    app = create_app()
    
    with app.app_context():
        # Wyczyść dane testowe
        clear_test_data()
        
        # Utwórz użytkownika testowego
        create_test_user()
        
        # Uruchom testy
        try:
            test_event_24h_plus()
            test_event_1h_plus()
            test_event_5min_plus()
            test_campaign_immediate()
            test_campaign_scheduled()
            test_priority_queue()
            
            print("\n" + "="*60)
            print("TESTY ZAKOŃCZONE")
            print("="*60)
            print("\n💡 Sprawdź kolejkę emaili w bazie danych (tabela email_queue)")
            print("💡 Uruchom processor aby wysłać emaile: python -m app.utils.process_email_queue")
            
        except Exception as e:
            print(f"\n❌ Błąd podczas testów: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()

