#!/usr/bin/env python3
"""
Skrypt do uruchamiania Celery Beat (scheduler)
"""

import os
import sys
from celery import Celery

# Dodaj ścieżkę do projektu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery_config import celery_app

if __name__ == '__main__':
    # Uruchom beat scheduler
    celery_app.start([
        'beat',
        '--loglevel=info',
        '--pidfile=celerybeat.pid',
        '--schedule=celerybeat-schedule'
    ])
