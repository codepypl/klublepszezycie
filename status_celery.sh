#!/bin/bash
# status_celery.sh - Sprawdzenie statusu systemu Celery

echo "📊 Status systemu Celery"
echo "========================"

# Sprawdź Redis
echo "🔍 Redis:"
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis działa"
    redis-cli info server | grep redis_version
else
    echo "❌ Redis nie działa"
fi

echo ""

# Sprawdź procesy Celery
echo "🔍 Procesy Celery:"
WORKER_COUNT=$(pgrep -f "celery.*worker" | wc -l)
BEAT_COUNT=$(pgrep -f "celery.*beat" | wc -l)
FLOWER_COUNT=$(pgrep -f "celery.*flower" | wc -l)

echo "Worker: $WORKER_COUNT procesów"
echo "Beat: $BEAT_COUNT procesów"
echo "Flower: $FLOWER_COUNT procesów"

echo ""

# Sprawdź logi
echo "📋 Ostatnie logi:"
if [ -f logs/celery_worker.log ]; then
    echo "Worker (ostatnie 5 linii):"
    tail -5 logs/celery_worker.log
fi

echo ""

# Sprawdź kolejki
echo "🔍 Kolejki Celery:"
cd /apps/klublepszezycie
source .venv/bin/activate
celery -A celery_app inspect active 2>/dev/null || echo "❌ Nie można połączyć się z Celery"

echo ""

# Sprawdź usługi systemd
echo "🔍 Usługi systemd:"
if systemctl is-active celery-worker > /dev/null 2>&1; then
    echo "✅ celery-worker: $(systemctl is-active celery-worker)"
else
    echo "⚠️ celery-worker: nie uruchomiony jako usługa"
fi

if systemctl is-active celery-beat > /dev/null 2>&1; then
    echo "✅ celery-beat: $(systemctl is-active celery-beat)"
else
    echo "⚠️ celery-beat: nie uruchomiony jako usługa"
fi

echo ""
echo "🌐 Flower monitoring: http://localhost:5555"
