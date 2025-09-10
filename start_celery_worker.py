#!/usr/bin/env python3
"""
Skrypt do uruchamiania Celery Worker
"""

import os
import sys
from celery import Celery

# Dodaj ścieżkę do projektu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery_config import celery_app

if __name__ == '__main__':
    # Uruchom worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--hostname=worker@%h'
    ])
