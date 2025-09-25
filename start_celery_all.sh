#!/bin/bash
# start_celery_all.sh - Uruchomienie wszystkich komponentów Celery

echo "🚀 Uruchamianie systemu email z Celery..."

# Sprawdź czy Redis działa
echo "1. Sprawdzanie Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis nie działa. Uruchamianie..."
    sudo systemctl start redis-server
    sleep 2
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "❌ Nie można uruchomić Redis. Sprawdź instalację."
        exit 1
    fi
fi
echo "✅ Redis działa"

# Aktywuj środowisko wirtualne
echo "2. Aktywacja środowiska wirtualnego..."
cd /apps/klublepszezycie
source .venv/bin/activate

# Sprawdź czy Celery jest zainstalowany
echo "3. Sprawdzanie Celery..."
if ! python -c "import celery" > /dev/null 2>&1; then
    echo "❌ Celery nie jest zainstalowany. Instalowanie..."
    pip install celery redis
fi
echo "✅ Celery zainstalowany"

# Uruchom Celery Worker w tle
echo "4. Uruchamianie Celery Worker..."
nohup celery -A celery_app worker --loglevel=info --concurrency=4 --queues=email_queue,event_queue,default > logs/celery_worker.log 2>&1 &
WORKER_PID=$!
echo "✅ Celery Worker uruchomiony (PID: $WORKER_PID)"

# Uruchom Celery Beat w tle
echo "5. Uruchamianie Celery Beat..."
nohup celery -A celery_app beat --loglevel=info > logs/celery_beat.log 2>&1 &
BEAT_PID=$!
echo "✅ Celery Beat uruchomiony (PID: $BEAT_PID)"

# Uruchom Flower w tle
echo "6. Uruchamianie Flower (monitoring)..."
nohup celery -A celery_app flower --port=5555 > logs/flower.log 2>&1 &
FLOWER_PID=$!
echo "✅ Flower uruchomiony (PID: $FLOWER_PID)"

# Zapisz PID do pliku
echo "$WORKER_PID" > celery_worker.pid
echo "$BEAT_PID" > celery_beat.pid
echo "$FLOWER_PID" > flower.pid

echo ""
echo "🎉 System Celery uruchomiony!"
echo "📊 Flower monitoring: http://localhost:5555"
echo "📋 Logi:"
echo "   - Worker: logs/celery_worker.log"
echo "   - Beat: logs/celery_beat.log"
echo "   - Flower: logs/flower.log"
echo ""
echo "🛑 Aby zatrzymać: ./stop_celery_all.sh"
echo "📊 Status: ./status_celery.sh"
