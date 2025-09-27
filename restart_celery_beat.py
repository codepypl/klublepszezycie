#!/usr/bin/env python3
"""
Script to restart Celery Beat and recreate scheduled tasks
"""
import os
import sys
import subprocess
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Restart Celery Beat and recreate tasks"""
    print("🔄 Restart Celery Beat i odtworzenie zadań...")
    print(f"⏰ Czas: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # 1. Stop Celery Beat
    print("🛑 Zatrzymywanie Celery Beat...")
    try:
        subprocess.run(['sudo', 'systemctl', 'stop', 'celery-beat'], check=True)
        print("✅ Celery Beat zatrzymany")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Błąd zatrzymywania Celery Beat: {e}")
    
    # 2. Clear schedule files
    print("\n🧹 Czyszczenie plików harmonogramu...")
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
    
    # 3. Start Celery Beat
    print("\n🚀 Uruchamianie Celery Beat...")
    try:
        subprocess.run(['sudo', 'systemctl', 'start', 'celery-beat'], check=True)
        print("✅ Celery Beat uruchomiony")
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd uruchamiania Celery Beat: {e}")
        return
    
    # 4. Wait for startup
    print("\n⏳ Oczekiwanie na uruchomienie...")
    time.sleep(5)
    
    # 5. Check status
    print("\n📊 Sprawdzanie statusu...")
    try:
        result = subprocess.run(['sudo', 'systemctl', 'is-active', 'celery-beat'], 
                              capture_output=True, text=True)
        if result.stdout.strip() == 'active':
            print("✅ Celery Beat: aktywny")
        else:
            print(f"❌ Celery Beat: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("❌ Błąd sprawdzania statusu Celery Beat")
    
    # 6. Check scheduled tasks
    print("\n🔍 Sprawdzanie zaplanowanych zadań...")
    try:
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
    
    print("\n" + "=" * 50)
    print("✅ Restart Celery Beat zakończony!")
    print("\n📋 Następne kroki:")
    print("   1. Uruchom: python3 recreate_celery_tasks.py")
    print("   2. Sprawdź logi: sudo journalctl -u celery-beat -f")
    print("   3. Monitoruj zadania w panelu admina")

if __name__ == "__main__":
    main()
