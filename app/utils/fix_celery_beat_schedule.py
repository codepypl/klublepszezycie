#!/usr/bin/env python3
"""
Skrypt do naprawy harmonogramu Celery Beat na serwerze produkcyjnym
Dodaje brakujące zadanie archiwizacji wydarzeń
"""
import os
import sys
import django
from datetime import timedelta

# Dodaj ścieżkę do aplikacji
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from celery_app import celery
from celery.schedules import crontab

def fix_celery_beat_schedule():
    """Napraw harmonogram Celery Beat"""
    try:
        print("🔧 Naprawiam harmonogram Celery Beat...")
        
        # Sprawdź aktualny harmonogram
        print("📋 Aktualny harmonogram:")
        beat_schedule = celery.conf.beat_schedule
        for name, task_info in beat_schedule.items():
            print(f"  - {name}: {task_info['task']} (co {task_info['schedule']}s)")
        
        # Sprawdź czy zadanie archiwizacji istnieje
        if 'archive-ended-events' in beat_schedule:
            print("✅ Zadanie 'archive-ended-events' już istnieje w harmonogramie")
        else:
            print("❌ Zadanie 'archive-ended-events' NIE istnieje w harmonogramie")
            print("🔧 Dodaję zadanie do harmonogramu...")
            
            # Dodaj zadanie do harmonogramu
            beat_schedule['archive-ended-events'] = {
                'task': 'app.tasks.event_tasks.archive_ended_events_task',
                'schedule': 600.0,  # Co 10 minut
            }
            
            # Zapisz konfigurację
            celery.conf.beat_schedule = beat_schedule
            print("✅ Zadanie dodane do harmonogramu")
        
        # Sprawdź ponownie
        print("\n📋 Zaktualizowany harmonogram:")
        for name, task_info in beat_schedule.items():
            print(f"  - {name}: {task_info['task']} (co {task_info['schedule']}s)")
        
        print("\n🔄 Aby zmiany zostały zastosowane, zrestartuj Celery Beat:")
        print("   sudo systemctl restart celerybeat")
        print("   lub")
        print("   sudo supervisorctl restart celerybeat")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd naprawy harmonogramu: {e}")
        return False

if __name__ == "__main__":
    success = fix_celery_beat_schedule()
    sys.exit(0 if success else 1)
