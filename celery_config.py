"""
Konfiguracja Celery dla automatycznego wysyłania emaili
"""

import os
from celery import Celery

# Konfiguracja Redis jako broker
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Utwórz instancję Celery
celery_app = Celery(
    'klublepszezycie',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks.email_tasks']
)

# Konfiguracja Celery
celery_app.conf.update(
    # Czasowe ustawienia
    timezone='Europe/Warsaw',
    enable_utc=True,
    
    # Harmonogram zadań
    beat_schedule={
        'process-email-schedules': {
            'task': 'tasks.email_tasks.process_email_schedules',
            'schedule': 300.0,  # Co 5 minut
        },
    },
    
    # Ustawienia workerów
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=True,
    
    # Retry ustawienia
    task_default_retry_delay=60,  # 1 minuta
    task_max_retries=3,
    
    # Serializacja
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)

# Konfiguracja logowania
import logging
from datetime import datetime

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Setup Celery logging
celery_app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    worker_log_file=os.path.join(logs_dir, 'celery_worker.log'),
    beat_log_file=os.path.join(logs_dir, 'celery_beat.log'),
    flower_log_file=os.path.join(logs_dir, 'celery_flower.log'),
    worker_log_level='INFO',
    beat_log_level='INFO',
    flower_log_level='INFO',
)