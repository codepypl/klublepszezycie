#!/usr/bin/env python3
"""
Skrypt do uruchamiania Celery Flower (monitoring)
"""

import os
import sys
from celery import Celery

# Dodaj ścieżkę do projektu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery_config import celery_app

if __name__ == '__main__':
    # Uruchom Flower
    celery_app.start([
        'flower',
        '--port=5555',
        '--broker=redis://localhost:6379/0'
    ])
