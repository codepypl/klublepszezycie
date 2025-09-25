#!/bin/bash
# Skrypt do uruchamiania Flower (monitoring Celery)

echo "🌸 Uruchamianie Flower..."

# Aktywuj środowisko wirtualne
source .venv/bin/activate

# Ustaw zmienne środowiskowe
export FLASK_APP=app
export FLASK_ENV=production

# Uruchom Flower
celery -A celery_app flower --port=5555
