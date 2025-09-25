#!/bin/bash
# Skrypt do uruchamiania Celery Worker

echo "🚀 Uruchamianie Celery Worker..."

# Aktywuj środowisko wirtualne
source .venv/bin/activate

# Ustaw zmienne środowiskowe
export FLASK_APP=app
export FLASK_ENV=production

# Uruchom Celery Worker - optymalizowane dla 1GB RAM (100MB wolnego)
celery -A celery_app worker --loglevel=error --concurrency=1 --queues=email_queue,event_queue --max-memory-per-child=100000 --max-tasks-per-child=10 --without-gossip --without-mingle --without-heartbeat
