#!/bin/bash
# Skrypt do uruchamiania Celery Beat (scheduler)

echo "⏰ Uruchamianie Celery Beat..."

# Aktywuj środowisko wirtualne
source .venv/bin/activate

# Ustaw zmienne środowiskowe
export FLASK_APP=app
export FLASK_ENV=production

# Uruchom Celery Beat
celery -A celery_app beat --loglevel=info
