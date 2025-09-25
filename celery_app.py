"""
Celery configuration for Lepsze Życie Club
"""
import os
from celery import Celery
from celery.schedules import crontab

# Konfiguracja Celery
def make_celery(app=None):
    if app is None:
        app_name = __name__
        broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        backend_url = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    else:
        app_name = app.import_name
        broker_url = app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        backend_url = app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    celery = Celery(
        app_name,
        broker=broker_url,
        backend=backend_url,
        include=[
            'app.tasks.email_tasks',
            'app.tasks.event_tasks'
        ]
    )
    
    # Konfiguracja - optymalizowana dla 1GB RAM
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Europe/Warsaw',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minut timeout
        task_soft_time_limit=25 * 60,  # 25 minut soft timeout
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_compression='gzip',
        result_compression='gzip',
        result_expires=3600,  # 1 godzina
        # Optymalizacje dla bardzo małej ilości RAM (50MB wolnego)
        worker_max_memory_per_child=50000,  # 50MB per worker - bardziej agresywne
        worker_max_tasks_per_child=5,  # Restart worker po 5 zadaniach - częściej
        worker_direct=True,  # Bezpośrednie połączenie z brokerem
        worker_disable_rate_limits=True,  # Wyłącz limity
        worker_send_task_events=False,  # Wyłącz eventy
        task_send_sent_event=False,  # Wyłącz sent eventy
        # Dodatkowe optymalizacje pamięci
        worker_pool_restarts=True,  # Pozwól na restart pool
        worker_hijack_root_logger=False,  # Nie przejmuj root loggera
        worker_log_color=False,  # Wyłącz kolory w logach
        worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',  # Prosty format
        task_routes={
            'app.tasks.email_tasks.*': {'queue': 'email_queue'},
            'app.tasks.event_tasks.*': {'queue': 'event_queue'},
        },
        task_default_queue='default',
        task_queues={
            'email_queue': {
                'exchange': 'email_queue',
                'routing_key': 'email_queue',
            },
            'event_queue': {
                'exchange': 'event_queue', 
                'routing_key': 'event_queue',
            },
            'default': {
                'exchange': 'default',
                'routing_key': 'default',
            },
        }
    )
    
    # Kontekst aplikacji Flask dla zadań Celery
    if app is not None:
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    # Zaplanowane zadania
    celery.conf.beat_schedule = {
        'process-email-queue': {
            'task': 'app.tasks.email_tasks.process_email_queue_task',
            'schedule': 30.0,  # Co 30 sekund
        },
        'process-scheduled-campaigns': {
            'task': 'app.tasks.email_tasks.process_scheduled_campaigns_task',
            'schedule': 60.0,  # Co minutę
        },
        'process-event-reminders': {
            'task': 'app.tasks.event_tasks.process_event_reminders_task',
            'schedule': 300.0,  # Co 5 minut
        },
    }
    
    return celery

# Utwórz instancję Celery
celery = make_celery()

if __name__ == '__main__':
    celery.start()
