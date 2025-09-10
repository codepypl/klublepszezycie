#!/usr/bin/env python3
"""
Skrypt do uruchamiania całego systemu emaili z Celery
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def start_process(command, log_file, name):
    """Uruchom proces w tle"""
    try:
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                command,
                stdout=f,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
        print(f"✅ {name} uruchomiony (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Błąd uruchamiania {name}: {e}")
        return None

def stop_processes():
    """Zatrzymaj wszystkie procesy"""
    print("🛑 Zatrzymywanie procesów...")
    
    # Zatrzymaj procesy po nazwie
    processes = ['celery', 'flower', 'python app.py']
    for process_name in processes:
        try:
            subprocess.run(['pkill', '-f', process_name], check=False)
            print(f"✅ Zatrzymano: {process_name}")
        except:
            pass

def main():
    """Główna funkcja"""
    print("🚀 Uruchamianie systemu automatycznego wysyłania emaili...")
    
    # Zatrzymaj istniejące procesy
    stop_processes()
    time.sleep(2)
    
    # Sprawdź czy Redis działa
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        if result.stdout.strip() != 'PONG':
            print("❌ Redis nie działa! Uruchom: brew services start redis")
            return
        print("✅ Redis działa")
    except:
        print("❌ Redis nie jest zainstalowany! Zainstaluj: brew install redis")
        return
    
    # Uruchom procesy
    processes = []
    
    # 1. Flask app
    flask_process = start_process(
        ['python', 'app.py'],
        'flask_app.log',
        'Flask App'
    )
    if flask_process:
        processes.append(flask_process)
    
    time.sleep(3)
    
    # 2. Celery Worker
    worker_process = start_process(
        ['python', 'start_celery_worker.py'],
        'celery_worker.log',
        'Celery Worker'
    )
    if worker_process:
        processes.append(worker_process)
    
    time.sleep(2)
    
    # 3. Celery Beat
    beat_process = start_process(
        ['python', 'start_celery_beat.py'],
        'celery_beat.log',
        'Celery Beat'
    )
    if beat_process:
        processes.append(beat_process)
    
    time.sleep(2)
    
    # 4. Flower (opcjonalnie)
    flower_process = start_process(
        ['python', 'start_celery_flower.py'],
        'celery_flower.log',
        'Flower (monitoring)'
    )
    if flower_process:
        processes.append(flower_process)
    
    print("\n🎉 System uruchomiony!")
    print("📊 Dostępne usługi:")
    print("  - Flask App: http://localhost:5000")
    print("  - Flower: http://localhost:5555")
    print("  - Redis: localhost:6379")
    print("\n📝 Logi:")
    print("  - Flask: flask_app.log")
    print("  - Celery Worker: celery_worker.log")
    print("  - Celery Beat: celery_beat.log")
    print("  - Flower: celery_flower.log")
    
    print("\n⏹️  Naciśnij Ctrl+C aby zatrzymać wszystkie procesy...")
    
    try:
        # Czekaj na sygnał przerwania
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Zatrzymywanie systemu...")
        stop_processes()
        print("✅ System zatrzymany")

if __name__ == "__main__":
    main()
