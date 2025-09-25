# 🚀 Instalacja i uruchomienie Celery

## 📋 Wymagania

- Python 3.13+
- Redis (broker i backend)
- Aplikacja Flask już skonfigurowana

## 🔧 Instalacja Redis

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### CentOS/RHEL:
```bash
sudo yum install redis
sudo systemctl start redis
sudo systemctl enable redis
```

### macOS (Homebrew):
```bash
brew install redis
brew services start redis
```

## 📦 Instalacja zależności Python

```bash
cd /apps/klublepszezycie
source .venv/bin/activate
pip install celery redis
```

## ⚙️ Konfiguracja

### 1. Zmienne środowiskowe
Dodaj do `.env`:
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 2. Sprawdź konfigurację
```bash
python -c "from app import create_app; app = create_app(); print('✅ Celery configured')"
```

## 🚀 Uruchomienie

### 1. Uruchom Redis
```bash
sudo systemctl start redis-server
sudo systemctl status redis-server
```

### 2. Uruchom Celery Worker
```bash
cd /apps/klublepszezycie
source .venv/bin/activate
celery -A celery_app worker --loglevel=info --concurrency=4 --queues=email_queue,event_queue,default
```

### 3. Uruchom Celery Beat (scheduler)
```bash
cd /apps/klublepszezycie
source .venv/bin/activate
celery -A celery_app beat --loglevel=info
```

### 4. Uruchom Flower (monitoring)
```bash
cd /apps/klublepszezycie
source .venv/bin/activate
celery -A celery_app flower --port=5555
```

## 🔄 Uruchomienie jako usługi systemd

### 1. Skopiuj pliki usług
```bash
sudo cp celery-worker.service /etc/systemd/system/
sudo cp celery-beat.service /etc/systemd/system/
```

### 2. Ustaw uprawnienia
```bash
sudo chmod 644 /etc/systemd/system/celery-worker.service
sudo chmod 644 /etc/systemd/system/celery-beat.service
```

### 3. Uruchom usługi
```bash
sudo systemctl daemon-reload
sudo systemctl start celery-worker
sudo systemctl start celery-beat
sudo systemctl enable celery-worker
sudo systemctl enable celery-beat
```

### 4. Sprawdź status
```bash
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

## 📊 Monitoring

### Flower (Web UI)
- URL: http://localhost:5555
- Monitoruje zadania, workerów, kolejki

### Logi
```bash
# Logi Celery Worker
sudo journalctl -u celery-worker -f

# Logi Celery Beat
sudo journalctl -u celery-beat -f

# Logi Redis
sudo journalctl -u redis-server -f
```

## 🧪 Testowanie

### 1. Test aplikacji Flask
```bash
curl -X POST http://localhost:8000/api/email/test-sending \
  -H "Content-Type: application/json" \
  -d '{"test_email": "test@example.com", "count": 5, "batch_size": 2}'
```

### 2. Test Celery bezpośrednio
```bash
python -c "
from app.tasks.email_tasks import test_email_sending_task
result = test_email_sending_task.delay('test@example.com', 5, 2)
print(f'Task ID: {result.id}')
"
```

## 🔧 Rozwiązywanie problemów

### Problem: Redis nie działa
```bash
sudo systemctl status redis-server
sudo systemctl restart redis-server
```

### Problem: Celery Worker nie startuje
```bash
celery -A celery_app worker --loglevel=debug
```

### Problem: Zadania nie są wykonywane
```bash
# Sprawdź połączenie z Redis
redis-cli ping

# Sprawdź kolejki
celery -A celery_app inspect active
```

### Problem: Brak uprawnień
```bash
sudo chown -R celery:celery /apps/klublepszezycie
sudo chmod +x /apps/klublepszezycie/.venv/bin/celery
```

## 📋 Zadania zaplanowane

Celery automatycznie wykonuje:

1. **Przetwarzanie kolejki emaili** - co 30 sekund
2. **Przetwarzanie zaplanowanych kampanii** - co minutę  
3. **Przetwarzanie przypomnień o wydarzeniach** - co 5 minut

## 🔄 Backup plan

Jeśli Celery nie działa, użyj cron job:
```bash
./setup_cron_backup.sh
```

## ✅ Sprawdzenie statusu

```bash
# Status wszystkich usług
sudo systemctl status flask.service celery-worker celery-beat redis-server

# Test API
curl http://localhost:8000/api/email/test-sending -X POST -H "Content-Type: application/json" -d '{"test_email": "test@example.com", "count": 1}'

# Monitorowanie w czasie rzeczywistym
watch -n 5 'sudo systemctl status celery-worker celery-beat'
```
