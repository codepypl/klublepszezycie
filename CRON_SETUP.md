# Konfiguracja Cron dla archiwizacji wydarzeń

## 🔧 Instrukcje instalacji:

### 1. Sprawdź ścieżkę do Pythona:
```bash
which python3
# Powinno pokazać: /apps/klublepszezycie/.venv/bin/python3
```

### 2. Sprawdź ścieżkę do skryptu:
```bash
ls -la /apps/klublepszezycie/app/utils/archive_ended_events.py
# Powinno pokazać plik
```

### 3. Przetestuj skrypt ręcznie:
```bash
cd /apps/klublepszezycie
/apps/klublepszezycie/.venv/bin/python3 app/utils/archive_ended_events.py
```

### 4. Dodaj do Cron (uruchamiaj co 5 minut):
```bash
sudo crontab -e
```

### 5. Dodaj tę linię:
```cron
# Archiwizuj zakończone wydarzenia co 5 minut
*/5 * * * * cd /apps/klublepszezycie && /apps/klublepszezycie/.venv/bin/python3 app/utils/archive_ended_events.py >> /var/log/archive_events.log 2>&1
```

### 6. Sprawdź logi:
```bash
# Sprawdź czy Cron działa
sudo systemctl status cron

# Sprawdź logi archiwizacji
tail -f /var/log/archive_events.log

# Sprawdź logi Cron
sudo tail -f /var/log/cron
```

## 📋 Co robi skrypt:

1. **Sprawdza wszystkie aktywne wydarzenia**
2. **Znajduje zakończone** (current_time > end_date)
3. **Dla każdego zakończonego wydarzenia:**
   - Usuwa wszystkich członków z grup
   - Usuwa grupy (hard delete)
   - Ustawia flagi: `is_published=False`, `is_active=False`, `is_archived=True`
4. **Loguje wszystkie operacje** do `/var/log/archive_events.log`

## 🔍 Monitoring:

```bash
# Sprawdź ostatnie uruchomienia
tail -20 /var/log/archive_events.log

# Sprawdź błędy
grep "ERROR\|❌" /var/log/archive_events.log

# Sprawdź sukcesy
grep "✅" /var/log/archive_events.log
```

## ⚙️ Opcjonalne ustawienia:

### Uruchamiaj co 2 minuty (bardziej agresywnie):
```cron
*/2 * * * * cd /apps/klublepszezycie && /apps/klublepszezycie/.venv/bin/python3 app/utils/archive_ended_events.py >> /var/log/archive_events.log 2>&1
```

### Uruchamiaj tylko w godzinach pracy (8-18):
```cron
*/5 8-18 * * * cd /apps/klublepszezycie && /apps/klublepszezycie/.venv/bin/python3 app/utils/archive_ended_events.py >> /var/log/archive_events.log 2>&1
```

### Rotacja logów (dodaj do /etc/logrotate.d/archive_events):
```
/var/log/archive_events.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
}
```
