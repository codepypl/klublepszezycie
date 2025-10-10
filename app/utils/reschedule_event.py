"""
Skrypt do reschedulingu przypomnień o wydarzeniu

Użyj gdy:
- Zmieniłeś datę wydarzenia
- Chcesz ponownie zaplanować przypomnienia
- Stare emaile są w kolejce z nieaktualnymi datami

Przykład użycia:
    python app/utils/reschedule_event.py 123
    
Gdzie 123 to ID wydarzenia
"""
import sys
import os

# Dodaj ścieżkę projektu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models import EventSchedule
from app.services.email_v2.queue.scheduler import EmailScheduler


def reschedule_event(event_id: int):
    """Reschedule przypomnień dla wydarzenia"""
    
    app = create_app()
    
    with app.app_context():
        # Sprawdź czy wydarzenie istnieje
        event = EventSchedule.query.get(event_id)
        
        if not event:
            print(f"❌ Wydarzenie o ID {event_id} nie zostało znalezione")
            return False
        
        print(f"\n📅 Wydarzenie: {event.title}")
        print(f"   Data: {event.event_date}")
        print(f"   Przypomnienia zaplanowane: {event.reminders_scheduled}")
        print()
        
        # Potwierdź
        confirm = input("Czy chcesz zreschedule'ować przypomnienia? (tak/nie): ")
        
        if confirm.lower() not in ['tak', 't', 'yes', 'y']:
            print("❌ Anulowano")
            return False
        
        # Reschedule
        scheduler = EmailScheduler()
        success, message = scheduler.reschedule_event_reminders(event_id)
        
        if success:
            print(f"\n✅ {message}")
            return True
        else:
            print(f"\n❌ {message}")
            return False


def list_events():
    """Lista aktywnych wydarzeń"""
    
    app = create_app()
    
    with app.app_context():
        events = EventSchedule.query.filter_by(
            is_active=True
        ).order_by(EventSchedule.event_date.asc()).all()
        
        if not events:
            print("Brak aktywnych wydarzeń")
            return
        
        print("\n📅 Aktywne wydarzenia:\n")
        print(f"{'ID':<6} {'Tytuł':<40} {'Data':<20} {'Scheduled'}")
        print("-" * 80)
        
        for event in events:
            date_str = event.event_date.strftime('%Y-%m-%d %H:%M')
            scheduled_flag = '✅' if event.reminders_scheduled else '❌'
            title = event.title[:37] + '...' if len(event.title) > 40 else event.title
            
            print(f"{event.id:<6} {title:<40} {date_str:<20} {scheduled_flag}")
        
        print()


def main():
    """Główna funkcja"""
    
    if len(sys.argv) < 2:
        print("""
Użycie:
    python app/utils/reschedule_event.py <event_id>   - Reschedule wydarzenia
    python app/utils/reschedule_event.py list         - Lista wydarzeń
    
Przykład:
    python app/utils/reschedule_event.py 123
    python app/utils/reschedule_event.py list
        """)
        sys.exit(1)
    
    if sys.argv[1] == 'list':
        list_events()
    else:
        try:
            event_id = int(sys.argv[1])
            reschedule_event(event_id)
        except ValueError:
            print(f"❌ Nieprawidłowe ID wydarzenia: {sys.argv[1]}")
            sys.exit(1)


if __name__ == '__main__':
    main()

