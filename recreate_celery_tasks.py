#!/usr/bin/env python3
"""
Script to recreate all Celery tasks after database reset
"""
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.email_automation import EmailAutomation
from app.models import EventSchedule, EmailCampaign, EmailQueue

def main():
    """Recreate all Celery tasks after database reset"""
    print("🔄 Odtwarzanie zadań Celery po resecie bazy danych...")
    print(f"⏰ Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Recreate event reminders
            print("📅 1. Odtwarzanie przypomnień o wydarzeniach...")
            recreate_event_reminders()
            
            # 2. Recreate scheduled campaigns
            print("\n📧 2. Odtwarzanie zaplanowanych kampanii...")
            recreate_scheduled_campaigns()
            
            # 3. Recreate email queue processing
            print("\n📬 3. Odtwarzanie przetwarzania kolejki emaili...")
            recreate_email_queue_processing()
            
            print("\n" + "=" * 60)
            print("✅ Odtwarzanie zadań Celery zakończone!")
            print("\n📋 Sprawdź zadania:")
            print("   celery -A celery_app inspect scheduled")
            print("   celery -A celery_app inspect active")
            
        except Exception as e:
            print(f"❌ Błąd: {str(e)}")

def recreate_event_reminders():
    """Recreate event reminders for all active future events"""
    try:
        from app.utils.timezone_utils import get_local_now
        now = get_local_now()
        
        future_events = EventSchedule.query.filter(
            EventSchedule.is_active == True,
            EventSchedule.is_published == True,
            EventSchedule.event_date > now.replace(tzinfo=None)
        ).order_by(EventSchedule.event_date.asc()).all()
        
        print(f"   🔍 Znaleziono {len(future_events)} aktywnych przyszłych wydarzeń")
        
        if not future_events:
            print("   ℹ️ Brak aktywnych przyszłych wydarzeń")
            return
        
        email_automation = EmailAutomation()
        recreated_count = 0
        
        for event in future_events:
            try:
                print(f"   📅 Przetwarzam: {event.title} ({event.event_date})")
                
                # Schedule reminders for this event
                success, message = email_automation.schedule_event_reminders(event.id, 'event_based')
                
                if success:
                    print(f"      ✅ {message}")
                    recreated_count += 1
                else:
                    print(f"      ❌ Błąd: {message}")
                    
            except Exception as e:
                print(f"      ❌ Błąd przetwarzania wydarzenia {event.id}: {str(e)}")
        
        print(f"   📊 Odtworzono przypomnienia dla {recreated_count}/{len(future_events)} wydarzeń")
        
    except Exception as e:
        print(f"   ❌ Błąd odtwarzania przypomnień: {str(e)}")

def recreate_scheduled_campaigns():
    """Recreate scheduled email campaigns"""
    try:
        from app.utils.timezone_utils import get_local_now
        now = get_local_now()
        
        # Find scheduled campaigns
        scheduled_campaigns = EmailCampaign.query.filter(
            EmailCampaign.is_active == True,
            EmailCampaign.scheduled_at > now,
            EmailCampaign.status == 'scheduled'
        ).all()
        
        print(f"   🔍 Znaleziono {len(scheduled_campaigns)} zaplanowanych kampanii")
        
        if not scheduled_campaigns:
            print("   ℹ️ Brak zaplanowanych kampanii")
            return
        
        for campaign in scheduled_campaigns:
            try:
                print(f"   📧 Kampania: {campaign.subject} (zaplanowana na {campaign.scheduled_at})")
                
                # The campaign will be processed by process_scheduled_campaigns_task
                # which runs every minute via Celery Beat
                print(f"      ✅ Kampania będzie przetworzona automatycznie")
                
            except Exception as e:
                print(f"      ❌ Błąd przetwarzania kampanii {campaign.id}: {str(e)}")
        
        print(f"   📊 {len(scheduled_campaigns)} kampanii będzie przetworzonych automatycznie")
        
    except Exception as e:
        print(f"   ❌ Błąd odtwarzania kampanii: {str(e)}")

def recreate_email_queue_processing():
    """Recreate email queue processing tasks"""
    try:
        # Count pending emails in queue
        pending_emails = EmailQueue.query.filter(
            EmailQueue.status == 'pending'
        ).count()
        
        print(f"   🔍 Znaleziono {pending_emails} emaili w kolejce")
        
        if pending_emails == 0:
            print("   ℹ️ Kolejka emaili jest pusta")
            return
        
        # The process_email_queue_task runs every 30 seconds via Celery Beat
        # and will automatically process pending emails
        print(f"   ✅ {pending_emails} emaili będzie przetworzonych automatycznie")
        print("   📋 Zadanie process_email_queue_task uruchamia się co 30 sekund")
        
    except Exception as e:
        print(f"   ❌ Błąd odtwarzania przetwarzania kolejki: {str(e)}")

if __name__ == "__main__":
    main()
