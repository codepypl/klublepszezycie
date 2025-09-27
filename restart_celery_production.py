#!/usr/bin/env python3
"""
Script to restart Celery on production and recreate scheduled tasks
"""
import os
import sys
import subprocess
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.email_automation import EmailAutomation
from app.models import EventSchedule

def main():
    """Main function to restart Celery and recreate tasks"""
    print("🚀 Rozpoczynam restart Celery na produkcji...")
    print(f"📅 Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # Step 1: Stop Celery services
    print("🛑 Zatrzymywanie usług Celery...")
    try:
        # Stop Celery Beat
        subprocess.run(['sudo', 'systemctl', 'stop', 'celery-beat'], check=True)
        print("✅ Celery Beat zatrzymany")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Błąd zatrzymywania Celery Beat: {e}")
    
    try:
        # Stop Celery Worker
        subprocess.run(['sudo', 'systemctl', 'stop', 'celery-worker'], check=True)
        print("✅ Celery Worker zatrzymany")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Błąd zatrzymywania Celery Worker: {e}")
    
    # Step 2: Clear Celery schedule files
    print("\n🧹 Czyszczenie plików harmonogramu Celery...")
    schedule_files = [
        'celerybeat-schedule',
        'celerybeat-schedule-shm', 
        'celerybeat-schedule-wal'
    ]
    
    for file in schedule_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ Usunięto {file}")
            except OSError as e:
                print(f"⚠️ Błąd usuwania {file}: {e}")
        else:
            print(f"ℹ️ {file} nie istnieje")
    
    # Step 3: Clear Redis queues (optional)
    print("\n🔄 Czyszczenie kolejek Redis...")
    try:
        # Clear all Redis databases
        subprocess.run(['redis-cli', 'FLUSHALL'], check=True)
        print("✅ Redis wyczyszczony")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Błąd czyszczenia Redis: {e}")
    
    # Step 4: Start Celery services
    print("\n🚀 Uruchamianie usług Celery...")
    try:
        # Start Celery Worker
        subprocess.run(['sudo', 'systemctl', 'start', 'celery-worker'], check=True)
        print("✅ Celery Worker uruchomiony")
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd uruchamiania Celery Worker: {e}")
        return
    
    try:
        # Start Celery Beat
        subprocess.run(['sudo', 'systemctl', 'start', 'celery-beat'], check=True)
        print("✅ Celery Beat uruchomiony")
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd uruchamiania Celery Beat: {e}")
        return
    
    # Step 5: Wait for services to start
    print("\n⏳ Oczekiwanie na uruchomienie usług...")
    import time
    time.sleep(10)
    
    # Step 6: Check service status
    print("\n📊 Sprawdzanie statusu usług...")
    try:
        result = subprocess.run(['sudo', 'systemctl', 'is-active', 'celery-worker'], 
                              capture_output=True, text=True)
        if result.stdout.strip() == 'active':
            print("✅ Celery Worker: aktywny")
        else:
            print(f"❌ Celery Worker: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("❌ Błąd sprawdzania statusu Celery Worker")
    
    try:
        result = subprocess.run(['sudo', 'systemctl', 'is-active', 'celery-beat'], 
                              capture_output=True, text=True)
        if result.stdout.strip() == 'active':
            print("✅ Celery Beat: aktywny")
        else:
            print(f"❌ Celery Beat: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("❌ Błąd sprawdzania statusu Celery Beat")
    
    # Step 7: Recreate event reminders
    print("\n📅 Odtwarzanie przypomnień o wydarzeniach...")
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
            
            if future_events:
                email_automation = EmailAutomation()
                recreated_count = 0
                
                for event in future_events:
                    try:
                        print(f"📅 Przetwarzam wydarzenie: {event.title} ({event.event_date})")
                        
                        # Schedule reminders for this event
                        success, message = email_automation.schedule_event_reminders(event.id, 'event_based')
                        
                        if success:
                            print(f"✅ {message}")
                            recreated_count += 1
                        else:
                            print(f"❌ Błąd: {message}")
                            
                    except Exception as e:
                        print(f"❌ Błąd przetwarzania wydarzenia {event.id}: {str(e)}")
                
                print(f"\n✅ Odtworzono przypomnienia dla {recreated_count}/{len(future_events)} wydarzeń")
            else:
                print("ℹ️ Brak aktywnych przyszłych wydarzeń do przetworzenia")
                
        except Exception as e:
            print(f"❌ Błąd odtwarzania przypomnień: {str(e)}")
    
    # Step 8: Final status check
    print("\n🔍 Sprawdzanie zadań w Celery...")
    try:
        # Check scheduled tasks
        result = subprocess.run(['celery', '-A', 'celery_app', 'inspect', 'scheduled'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Celery Beat działa poprawnie")
            if result.stdout.strip():
                print("📋 Zaplanowane zadania:")
                print(result.stdout)
            else:
                print("ℹ️ Brak zaplanowanych zadań")
        else:
            print(f"❌ Błąd sprawdzania zadań: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout przy sprawdzaniu zadań Celery")
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd sprawdzania zadań: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Restart Celery zakończony!")
    print("📋 Następne kroki:")
    print("   1. Sprawdź logi: sudo journalctl -u celery-worker -f")
    print("   2. Sprawdź logi: sudo journalctl -u celery-beat -f")
    print("   3. Monitoruj zadania w panelu admina")
    print("   4. Sprawdź czy przypomnienia są planowane poprawnie")

if __name__ == "__main__":
    main()
