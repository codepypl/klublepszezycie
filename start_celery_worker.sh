#!/bin/bash
# Skrypt do uruchamiania Celery Worker

echo "🚀 Uruchamianie Celery Worker..."

# Aktywuj środowisko wirtualne
source .venv/bin/activate

# Ustaw zmienne środowiskowe
export FLASK_APP=app
export FLASK_ENV=production

# Uruchom Celery Worker
celery -A celery_app worker --loglevel=info --concurrency=4 --queues=email_queue,event_queue,default
