apt-get install# Instalacja i uruchomienie systemu mailingowego z Celery

## 🎯 Przegląd systemu

System mailingowy został rozszerzony o:
- ✅ **Celery** - asynchroniczne przetwarzanie emaili
- ✅ **Inteligentne planowanie** - automatyczne dostosowanie czasu wysyłki dla dużych grup
- ✅ **Obsługa zmiany godziny wydarzenia** - automatyczne anulowanie i planowanie nowych powiadomień
- ✅ **Batch processing** - wydajne wysyłanie w paczkach
- ✅ **Monitoring** - Flower do monitorowania zadań

## 📋 Wymagania

- Python 3.13+
- Redis (broker dla Celery)
- PostgreSQL (baza danych)
- Nginx (opcjonalnie, dla produkcji)

## 🚀 Instalacja krok po kroku

### 1. Instalacja Redis

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# CentOS/RHEL
sudo yum install redis
# lub
sudo dnf install redis

# macOS (Homebrew)
brew install redis

# Uruchom Redis
sudo systemctl start redis
sudo systemctl enable redis

# Sprawdź status
redis-cli ping
# Powinno zwrócić: PONG
```

### 2. Konfiguracja środowiska

```bash
# Przejdź do katalogu projektu
cd /path/to/klublepszezycie

# Aktywuj środowisko wirtualne
source .venv/bin/activate

# Zainstaluj zależności (jeśli jeszcze nie)
uv sync

# Dodaj zmienne środowiskowe do .env
echo "CELERY_BROKER_URL=redis://localhost:6379/0" >> .env
echo "CELERY_RESULT_BACKEND=redis://localhost:6379/0" >> .env
echo "EMAIL_QUEUE_BATCH_SIZE=50" >> .env
echo "EMAIL_QUEUE_DELAY=1" >> .env
```

### 3. Migracja bazy danych

```bash
# Uruchom migracje
flask db upgrade

# Sprawdź czy tabele zostały utworzone
psql -d your_database -c "\dt" | grep email
```

### 4. Test konfiguracji

```bash
# Test połączenia z Redis
python -c "import redis; r = redis.Redis(); print('Redis OK:', r.ping())"

# Test importu Celery
python -c "from celery_app import celery; print('Celery OK')"
```

## 🏃‍♂️ Uruchomienie systemu

### Opcja A: Ręczne uruchomienie (development)

```bash
# Terminal 1 - Flask aplikacja
source .venv/bin/activate
export FLASK_APP=app
export FLASK_ENV=production
flask run --host=0.0.0.0 --port=5000

# Terminal 2 - Celery Worker
./start_celery_worker.sh

# Terminal 3 - Celery Beat (scheduler)
./start_celery_worker.sh

# Terminal 4 - Flower (monitoring, opcjonalnie)
./start_flower.sh
```

### Opcja B: Systemd (produkcja)

```bash
# Skopiuj pliki service do systemd
sudo cp celery-worker.service /etc/systemd/system/
sudo cp celery-beat.service /etc/systemd/system/

# Edytuj ścieżki w plikach service (dostosuj do swojego serwera)
sudo nano /etc/systemd/system/celery-worker.service
sudo nano /etc/systemd/system/celery-beat.service

# Przeładuj systemd
sudo systemctl daemon-reload

# Uruchom serwisy
sudo systemctl start celery-worker
sudo systemctl start celery-beat

# Włącz automatyczne uruchamianie
sudo systemctl enable celery-worker
sudo systemctl enable celery-beat

# Sprawdź status
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

### Opcja C: Supervisor (alternatywa)

```bash
# Zainstaluj supervisor
sudo apt install supervisor  # Ubuntu/Debian
# lub
sudo yum install supervisor  # CentOS/RHEL

# Utwórz pliki konfiguracyjne
sudo nano /etc/supervisor/conf.d/celery-worker.conf
sudo nano /etc/supervisor/conf.d/celery-beat.conf

# Przeładuj konfigurację
sudo supervisorctl reread
sudo supervisorctl update

# Uruchom procesy
sudo supervisorctl start celery-worker
sudo supervisorctl start celery-beat

# Sprawdź status
sudo supervisorctl status
```

## 🧪 Test systemu

### 1. Test podstawowy

```bash
# Uruchom test wysyłania emaili
python test_email_sending.py
```

### 2. Test przez API

```bash
# Test wysyłania 100 emaili
curl -X POST http://localhost:5000/api/email/test-sending \
  -H "Content-Type: application/json" \
  -d '{
    "test_email": "codeitpy@gmail.com",
    "count": 100,
    "batch_size": 10
  }'
```

### 3. Monitoring

- **Flower**: http://localhost:5555
- **Logi Celery**: `tail -f /var/log/celery/worker.log`
- **Status systemd**: `sudo systemctl status celery-worker`

## 📊 Konfiguracja dla różnych scenariuszy

### Dla 600 uczestników

```bash
# W .env
EMAIL_QUEUE_BATCH_SIZE=50
EMAIL_QUEUE_DELAY=1

# Czas wysyłki: 600/50 = 12 paczek
# 12 * 50 * 1s = 600s = 10 minut + 20% bufora = 12 minut
# System automatycznie wyśle 2h12min przed wydarzeniem
```

### Dla 1000+ uczestników

```bash
# W .env
EMAIL_QUEUE_BATCH_SIZE=100
EMAIL_QUEUE_DELAY=0.5

# Zwiększ concurrency w start_celery_worker.sh
# --concurrency=8
```

## 🔧 Rozwiązywanie problemów

### Problem: Celery nie łączy się z Redis

```bash
# Sprawdź Redis
redis-cli ping

# Sprawdź logi
sudo journalctl -u celery-worker -f
```

### Problem: Zadania nie są wykonywane

```bash
# Sprawdź czy Beat jest uruchomiony
sudo systemctl status celery-beat

# Sprawdź logi Beat
sudo journalctl -u celery-beat -f
```

### Problem: Błędy w zadaniach

```bash
# Sprawdź logi Worker
sudo journalctl -u celery-worker -f

# Sprawdź w Flower
# http://localhost:5555/tasks
```

## 📈 Monitoring i logi

### Logi systemd

```bash
# Wszystkie logi Celery
sudo journalctl -u celery-worker -u celery-beat -f

# Tylko błędy
sudo journalctl -u celery-worker -u celery-beat -p err

# Logi z ostatniej godziny
sudo journalctl -u celery-worker -u celery-beat --since "1 hour ago"
```

### Monitoring przez Flower

1. Otwórz http://localhost:5555
2. Sprawdź zakładkę "Tasks" - status zadań
3. Sprawdź zakładkę "Workers" - status workerów
4. Sprawdź zakładkę "Monitor" - statystyki

## 🚨 Ważne uwagi

1. **Redis musi być uruchomiony** przed Celery
2. **Baza danych musi być dostępna** dla zadań
3. **Flask aplikacja musi być uruchomiona** dla kontekstu
4. **Beat i Worker** to osobne procesy - oba muszą być uruchomione
5. **Logi są kluczowe** - monitoruj je regularnie

## 📞 Wsparcie

W przypadku problemów:
1. Sprawdź logi systemd
2. Sprawdź Flower monitoring
3. Sprawdź połączenie z Redis
4. Sprawdź konfigurację w .env

---

**Gotowe!** 🎉 System mailingowy z Celery jest skonfigurowany i gotowy do użycia.
