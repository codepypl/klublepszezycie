# 📧 System Automatycznego Wysyłania Emaili

## 🎯 Przegląd

System wykorzystuje **Celery** do automatycznego wysyłania emaili zamiast cron'a. Oferuje:

- ✅ **Asynchroniczne przetwarzanie** - nie blokuje aplikacji Flask
- ✅ **Retry mechanizm** - automatyczne ponowne próby przy błędach
- ✅ **Monitoring** - śledzenie zadań przez Flower
- ✅ **Skalowalność** - można uruchomić wiele workerów
- ✅ **Harmonogramy** - automatyczne wysyłanie co 5 minut

## 🏗️ Architektura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask App     │    │  Celery Beat    │    │ Celery Worker   │
│   (Web Server)  │───▶│  (Scheduler)    │───▶│  (Email Sender) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │   Flower        │
│   (Database)    │    │   (Message      │    │  (Monitoring)   │
│                 │    │    Broker)      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Uruchamianie

### Opcja 1: Automatyczne (zalecane)
```bash
./start_email_system.py
```

### Opcja 2: Ręczne
```bash
# 1. Uruchom Redis
brew services start redis

# 2. Uruchom Flask App
python app.py &

# 3. Uruchom Celery Worker
python start_celery_worker.py &

# 4. Uruchom Celery Beat
python start_celery_beat.py &

# 5. Uruchom Flower (opcjonalnie)
python start_celery_flower.py &
```

## 📊 Monitoring

### Flower (Web UI)
- **URL**: http://localhost:5555
- **Funkcje**: 
  - Przeglądanie zadań
  - Statystyki wykonania
  - Logi błędów
  - Monitoring workerów

### Logi
- **Flask App**: `flask_app.log`
- **Celery Worker**: `celery_worker.log`
- **Celery Beat**: `celery_beat.log`
- **Flower**: `celery_flower.log`

## 🔧 Konfiguracja

### Harmonogramy EmailSchedule
```python
# Automatyczne wysyłanie co 5 minut
beat_schedule={
    'process-email-schedules': {
        'task': 'tasks.email_tasks.process_email_schedules',
        'schedule': 300.0,  # 5 minut
    },
}
```

### Typy Harmonogramów
1. **Email Powitalny** - przy aktywacji konta
2. **Potwierdzenie Zapisu** - przy rejestracji na wydarzenie
3. **Powiadomienie Admina** - o nowej rejestracji
4. **Przypomnienia Wydarzeń** - 24h, 1h, 5min przed

## 📝 Użycie

### Wysyłanie Natychmiastowe
```python
from app import schedule_immediate_email

# Wyślij email natychmiast
result = schedule_immediate_email(
    template_name='user_activation',
    recipient_email='user@example.com',
    variables={'name': 'Jan', 'activation_link': '...'}
)
```

### Wysyłanie Masowe
```python
from app import schedule_bulk_email

# Wyślij do wielu odbiorców
result = schedule_bulk_email(
    template_name='event_reminder_24h_before',
    recipient_emails=['user1@example.com', 'user2@example.com'],
    variables={'event_title': 'Spotkanie', 'event_date': '2025-09-15'}
)
```

## 🛠️ Rozwiązywanie Problemów

### Redis nie działa
```bash
brew services start redis
# lub
redis-server
```

### Celery Worker nie przetwarza zadań
```bash
# Sprawdź logi
tail -f celery_worker.log

# Restart worker
pkill -f celery
python start_celery_worker.py &
```

### Harmonogramy nie są wysyłane
```bash
# Sprawdź czy Beat działa
ps aux | grep beat

# Sprawdź logi Beat
tail -f celery_beat.log
```

## 📈 Statystyki

### Sprawdzenie Statusu
```python
from tasks.email_tasks import process_email_schedules

# Uruchom ręcznie
result = process_email_schedules.delay()
print(result.get())
```

### Monitoring w Flower
- Otwórz http://localhost:5555
- Sprawdź zakładkę "Tasks"
- Monitoruj "Workers"

## 🔄 Restart Systemu

```bash
# Zatrzymaj wszystkie procesy
pkill -f "python.*app.py"
pkill -f celery
pkill -f flower

# Uruchom ponownie
./start_email_system.py
```

## 📋 Wymagania

- Python 3.8+
- Redis
- PostgreSQL
- Celery
- Flower (opcjonalnie)

## 🎉 Korzyści vs Cron

| Funkcja | Cron | Celery |
|---------|------|--------|
| Asynchroniczność | ❌ | ✅ |
| Retry | ❌ | ✅ |
| Monitoring | ❌ | ✅ |
| Skalowalność | ❌ | ✅ |
| Integracja z Flask | ❌ | ✅ |
| Zarządzanie błędami | ❌ | ✅ |
