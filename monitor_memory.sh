#!/bin/bash
# Skrypt monitorowania pamięci dla serwera produkcyjnego

echo "🔍 Monitoring pamięci systemu..."
echo "=================================="

# Sprawdź użycie pamięci
echo "📊 Użycie pamięci:"
free -h

echo ""
echo "📈 Top 10 procesów używających najwięcej pamięci:"
ps aux --sort=-%mem | head -11

echo ""
echo "🔍 Procesy Celery:"
ps aux | grep celery

echo ""
echo "⚠️  Ostatnie zabicia przez OOM Killer:"
sudo dmesg | grep -i "killed process" | tail -5

echo ""
echo "📊 Użycie swap:"
swapon --show

echo ""
echo "💾 Dostępne miejsce na dysku:"
df -h /

echo ""
echo "🔄 Status systemd dla Celery:"
systemctl status celery-worker.service --no-pager -l

echo ""
echo "📝 Ostatnie logi Celery:"
journalctl -u celery-worker.service --no-pager -l -n 10
