"""
Celery configuration for Lepsze Życie Club
"""
import os
from celery import Celery
from celery.schedules import crontab

# Konfiguracja Celery
def make_celery(app_name=__name__):
    celery = Celery(
        app_name,
        broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        include=[
            'app.tasks.email_tasks',
            'app.tasks.event_tasks'
        ]
    )
    
    # Konfiguracja
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
        worker_disable_rate_limits=False,
        task_compression='gzip',
        result_compression='gzip',
        result_expires=3600,  # 1 godzina
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
