#!/bin/bash
# stop_celery_all.sh - Zatrzymanie wszystkich komponentów Celery

echo "🛑 Zatrzymywanie systemu Celery..."

# Zatrzymaj procesy z plików PID
if [ -f celery_worker.pid ]; then
    WORKER_PID=$(cat celery_worker.pid)
    if kill -0 $WORKER_PID 2>/dev/null; then
        echo "🛑 Zatrzymywanie Celery Worker (PID: $WORKER_PID)..."
        kill $WORKER_PID
        rm celery_worker.pid
        echo "✅ Celery Worker zatrzymany"
    else
        echo "⚠️ Celery Worker już nie działa"
        rm celery_worker.pid
    fi
fi

if [ -f celery_beat.pid ]; then
    BEAT_PID=$(cat celery_beat.pid)
    if kill -0 $BEAT_PID 2>/dev/null; then
        echo "🛑 Zatrzymywanie Celery Beat (PID: $BEAT_PID)..."
        kill $BEAT_PID
        rm celery_beat.pid
        echo "✅ Celery Beat zatrzymany"
    else
        echo "⚠️ Celery Beat już nie działa"
        rm celery_beat.pid
    fi
fi

if [ -f flower.pid ]; then
    FLOWER_PID=$(cat flower.pid)
    if kill -0 $FLOWER_PID 2>/dev/null; then
        echo "🛑 Zatrzymywanie Flower (PID: $FLOWER_PID)..."
        kill $FLOWER_PID
        rm flower.pid
        echo "✅ Flower zatrzymany"
    else
        echo "⚠️ Flower już nie działa"
        rm flower.pid
    fi
fi

# Zatrzymaj wszystkie procesy Celery
echo "🛑 Zatrzymywanie wszystkich procesów Celery..."
pkill -f "celery.*worker"
pkill -f "celery.*beat"
pkill -f "celery.*flower"

echo "✅ System Celery zatrzymany"
