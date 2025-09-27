#!/usr/bin/env python3
"""
Script to recreate event reminders for all active future events
"""
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.email_automation import EmailAutomation
from app.models import EventSchedule

def main():
    """Recreate event reminders for all active future events"""
    print("📅 Odtwarzanie przypomnień o wydarzeniach...")
    print(f"⏰ Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get all active future events
            from app.utils.timezone_utils import get_local_now
            now = get_local_now()
            
            future_events = EventSchedule.query.filter(
                EventSchedule.is_active == True,
                EventSchedule.is_published == True,
                EventSchedule.event_date > now.replace(tzinfo=None)
            ).order_by(EventSchedule.event_date.asc()).all()
            
            print(f"🔍 Znaleziono {len(future_events)} aktywnych przyszłych wydarzeń")
            
            if not future_events:
                print("ℹ️ Brak aktywnych przyszłych wydarzeń")
                return
            
            email_automation = EmailAutomation()
            recreated_count = 0
            failed_count = 0
            
            for event in future_events:
                try:
                    print(f"\n📅 Przetwarzam: {event.title}")
                    print(f"   📍 Data: {event.event_date}")
                    print(f"   📍 Lokalizacja: {event.location or 'Online'}")
                    
                    # Schedule reminders for this event
                    success, message = email_automation.schedule_event_reminders(event.id, 'event_based')
                    
                    if success:
                        print(f"   ✅ {message}")
                        recreated_count += 1
                    else:
                        print(f"   ❌ Błąd: {message}")
                        failed_count += 1
                        
                except Exception as e:
                    print(f"   ❌ Błąd przetwarzania wydarzenia {event.id}: {str(e)}")
                    failed_count += 1
            
            print("\n" + "=" * 50)
            print(f"📊 Podsumowanie:")
            print(f"   ✅ Pomyślnie: {recreated_count}")
            print(f"   ❌ Błędy: {failed_count}")
            print(f"   📋 Łącznie: {len(future_events)}")
            
            if recreated_count > 0:
                print(f"\n🎉 Odtworzono przypomnienia dla {recreated_count} wydarzeń!")
                print("📋 Sprawdź zadania w Celery:")
                print("   celery -A celery_app inspect scheduled")
            else:
                print("\n⚠️ Nie udało się odtworzyć żadnych przypomnień")
                
        except Exception as e:
            print(f"❌ Błąd: {str(e)}")

if __name__ == "__main__":
    main()
