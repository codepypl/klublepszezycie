#!/usr/bin/env python3
"""
Skrypt do restartu Celery - czyści kolejkę, wyłącza, usuwa bazę i włącza ponownie
"""

import sys
import os
import subprocess
import time
import signal
import psutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import create_app, db
from app.models.email_model import EmailQueue
from app.services.celery_cleanup import CeleryCleanupService

def clear_email_queue():
    """Czyści kolejkę emaili w bazie danych w BEZPIECZNY sposób.
    
    Domyślnie:
      - NIE usuwa e-maili w statusie 'pending' (aby nie gubić zaplanowanych wysyłek).
      - Usuwa tylko e-maile w statusie 'processing' starsze niż 30 minut (potencjalnie zawieszone).
      - Pełne czyszczenie (w tym 'pending') wymaga ustawienia zmiennej środowiskowej FORCE_CLEAR_EMAIL_QUEUE=true.
    """
    app = create_app()
    
    with app.app_context():
        force_clear = os.getenv('FORCE_CLEAR_EMAIL_QUEUE', 'false').lower() == 'true'
        print('🧹 Czyszczę kolejkę emaili w bazie danych...')
        print(f'   FORCE_CLEAR_EMAIL_QUEUE={force_clear}')

        if not force_clear:
            # Bezpieczny tryb: tylko sprzątanie zawieszonych 'processing'
            from app.utils.timezone_utils import get_local_now
            from datetime import timedelta
            cutoff = get_local_now() - timedelta(minutes=30)

            stuck_processing = EmailQueue.query.filter(
                EmailQueue.status == 'processing',
                EmailQueue.updated_at < cutoff
            ).all()

            print(f"📧 Zawieszone 'processing' do usunięcia: {len(stuck_processing)}")
            removed = 0
            for email in stuck_processing:
                print(f"  - Usuwam (processing): {email.recipient_email} | updated_at={email.updated_at}")
                db.session.delete(email)
                removed += 1

            db.session.commit()
            print(f'✅ Usunięto {removed} zawieszonych emaili (processing).')
            print("ℹ️ Aby usunąć także 'pending', ustaw FORCE_CLEAR_EMAIL_QUEUE=true na czas restartu.")
            return

        # Tryb wymuszony: usuń 'pending' i 'processing'
        pending_and_processing = EmailQueue.query.filter(
            EmailQueue.status.in_(['pending', 'processing'])
        ).all()

        print(f'📧 Znaleziono {len(pending_and_processing)} emaili do usunięcia (pending/processing)')

        if pending_and_processing:
            for email in pending_and_processing:
                print(f'  - Usuwam: {email.recipient_email} | status={email.status}')
                db.session.delete(email)
            db.session.commit()
            print(f'✅ Usunięto {len(pending_and_processing)} emaili z kolejki')
        else:
            print('✅ Brak emaili do usunięcia (pending/processing)')

def stop_celery_workers():
    """Zatrzymuje wszystkie procesy Celery"""
    print('🛑 Zatrzymuję procesy Celery...')
    
    celery_processes = []
    
    # Znajdź procesy Celery
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'celery' in cmdline.lower() and 'worker' in cmdline.lower():
                celery_processes.append(proc)
                print(f'  - Znaleziono proces Celery: PID {proc.info["pid"]}')
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Zatrzymaj procesy
    for proc in celery_processes:
        try:
            print(f'  - Zatrzymuję proces {proc.info["pid"]}...')
            proc.terminate()
            proc.wait(timeout=10)
            print(f'  ✅ Proces {proc.info["pid"]} zatrzymany')
        except psutil.TimeoutExpired:
            print(f'  ⚠️  Proces {proc.info["pid"]} nie zatrzymał się, używam SIGKILL...')
            proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f'  ⚠️  Nie można zatrzymać procesu {proc.info["pid"]}: {e}')
    
    if not celery_processes:
        print('✅ Brak procesów Celery do zatrzymania')

def clear_celery_database():
    """Czyści bazę danych Celery (Redis)"""
    print('🗑️  Czyszczę bazę danych Celery...')
    
    try:
        import redis
        from app.config.config import get_config
        
        config = get_config()
        redis_url = config.CELERY_BROKER_URL
        
        # Połącz z Redis
        r = redis.from_url(redis_url)
        
        # Wyczyść wszystkie klucze
        keys = r.keys('celery*')
        if keys:
            r.delete(*keys)
            print(f'✅ Usunięto {len(keys)} kluczy z Redis')
        else:
            print('✅ Baza Redis jest już pusta')
            
    except Exception as e:
        print(f'❌ Błąd czyszczenia Redis: {e}')

def start_celery_workers():
    """Uruchamia procesy Celery"""
    print('🚀 Uruchamiam procesy Celery...')
    
    try:
        # Uruchom Celery worker w tle
        worker_cmd = [
            'celery', '-A', 'celery_app', 'worker',
            '--loglevel=info',
            '--concurrency=2',
            '--queues=email_queue,event_queue,default'
        ]
        
        print(f'  - Uruchamiam: {" ".join(worker_cmd)}')
        
        # Uruchom w tle
        process = subprocess.Popen(
            worker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        print(f'  ✅ Celery worker uruchomiony (PID: {process.pid})')
        
        # Uruchom Celery beat w tle
        beat_cmd = [
            'celery', '-A', 'celery_app', 'beat',
            '--loglevel=info'
        ]
        
        print(f'  - Uruchamiam: {" ".join(beat_cmd)}')
        
        beat_process = subprocess.Popen(
            beat_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        print(f'  ✅ Celery beat uruchomiony (PID: {beat_process.pid})')
        
        # Poczekaj chwilę
        time.sleep(3)
        
        # Sprawdź czy procesy działają
        if process.poll() is None:
            print('✅ Celery worker działa poprawnie')
        else:
            print('❌ Celery worker nie uruchomił się poprawnie')
        
        if beat_process.poll() is None:
            print('✅ Celery beat działa poprawnie')
        else:
            print('❌ Celery beat nie uruchomił się poprawnie')
        
    except Exception as e:
        print(f'❌ Błąd uruchamiania Celery: {e}')

def verify_celery_status():
    """Weryfikuje status Celery"""
    print('🔍 Weryfikuję status Celery...')
    
    try:
        from celery_app import celery
        inspect = celery.control.inspect()
        
        # Sprawdź workerów
        stats = inspect.stats()
        if stats:
            print(f'✅ Celery działa - {len(stats)} workerów')
            for worker_name in stats.keys():
                print(f'  - Worker: {worker_name}')
        else:
            print('❌ Brak aktywnych workerów Celery')
        
        # Sprawdź zadania
        scheduled = inspect.scheduled()
        active = inspect.active()
        
        total_scheduled = sum(len(tasks) for tasks in (scheduled or {}).values())
        total_active = sum(len(tasks) for tasks in (active or {}).values())
        
        print(f'📊 Status zadań:')
        print(f'  - Zaplanowane: {total_scheduled}')
        print(f'  - Aktywne: {total_active}')
        
    except Exception as e:
        print(f'❌ Błąd weryfikacji Celery: {e}')

def restart_celery():
    """Główna funkcja restartu Celery"""
    print('🔄 Rozpoczynam restart Celery...')
    
    try:
        # 1. Wyczyść kolejkę emaili
        clear_email_queue()
        
        # 2. Zatrzymaj procesy Celery
        stop_celery_workers()
        
        # 3. Poczekaj chwilę
        print('⏳ Czekam 5 sekund...')
        time.sleep(5)
        
        # 4. Wyczyść bazę danych Celery
        clear_celery_database()
        
        # 5. Uruchom procesy Celery
        start_celery_workers()
        
        # 6. Poczekaj chwilę
        print('⏳ Czekam 5 sekund...')
        time.sleep(5)
        
        # 7. Weryfikuj status
        verify_celery_status()
        
        print('\\n🎉 Restart Celery zakończony!')
        
    except Exception as e:
        print(f'❌ Błąd podczas restartu: {e}')
        return False
    
    return True

def main():
    """Główna funkcja"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print('Użycie: python restart_celery.py')
        print('Funkcje:')
        print('  - Czyści kolejkę emaili w bazie danych')
        print('  - Zatrzymuje wszystkie procesy Celery')
        print('  - Czyści bazę danych Celery (Redis)')
        print('  - Uruchamia procesy Celery ponownie')
        print('  - Weryfikuje status')
        sys.exit(0)
    
    print('⚠️  UWAGA: Ten skrypt zatrzyma i uruchomi ponownie Celery!')
    print('Czy chcesz kontynuować? (tak/nie): ', end='')
    
    response = input().lower().strip()
    if response not in ['tak', 'yes', 'y', 't']:
        print('❌ Anulowano')
        sys.exit(0)
    
    restart_celery()

if __name__ == '__main__':
    main()
