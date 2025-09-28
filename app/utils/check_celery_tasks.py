#!/usr/bin/env python3
"""
Skrypt do sprawdzenia zadań Celery na serwerze
"""
import os
import sys

# Dodaj ścieżkę do aplikacji
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from celery_app import celery

def check_celery_tasks():
    """Sprawdź zadania Celery"""
    try:
        print("🔍 Sprawdzam zadania Celery...")
        
        # Sprawdź zarejestrowane zadania
        print("\n📋 Zarejestrowane zadania:")
        registered_tasks = celery.tasks.keys()
        for task in sorted(registered_tasks):
            if not task.startswith('celery.'):
                print(f"  - {task}")
        
        # Sprawdź harmonogram Beat
        print("\n⏰ Harmonogram Celery Beat:")
        beat_schedule = celery.conf.beat_schedule
        if beat_schedule:
            for name, task_info in beat_schedule.items():
                schedule = task_info['schedule']
                if hasattr(schedule, 'total_seconds'):
                    schedule_str = f"co {schedule.total_seconds()}s"
                else:
                    schedule_str = str(schedule)
                print(f"  - {name}: {task_info['task']} ({schedule_str})")
        else:
            print("  ❌ Brak zadań w harmonogramie Beat")
        
        # Sprawdź aktywne zadania
        print("\n🔄 Aktywne zadania:")
        try:
            inspect = celery.control.inspect()
            active = inspect.active()
            if active:
                for worker, tasks in active.items():
                    print(f"  Worker {worker}:")
                    for task in tasks:
                        print(f"    - {task['name']} (ID: {task['id']})")
            else:
                print("  Brak aktywnych zadań")
        except Exception as e:
            print(f"  ❌ Błąd sprawdzania aktywnych zadań: {e}")
        
        # Sprawdź zaplanowane zadania
        print("\n📅 Zaplanowane zadania:")
        try:
            scheduled = inspect.scheduled()
            if scheduled:
                for worker, tasks in scheduled.items():
                    print(f"  Worker {worker}:")
                    for task in tasks:
                        print(f"    - {task['name']} (ID: {task['id']})")
            else:
                print("  Brak zaplanowanych zadań")
        except Exception as e:
            print(f"  ❌ Błąd sprawdzania zaplanowanych zadań: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd sprawdzania zadań Celery: {e}")
        return False

if __name__ == "__main__":
    success = check_celery_tasks()
    sys.exit(0 if success else 1)
