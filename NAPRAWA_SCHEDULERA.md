# Naprawa Email Schedulera - Instrukcja

## Co zostało naprawione?

### ✅ Problem 1: Celery taski nie uruchamiają się

**Zmieniono:**
- Dodano szczegółowe logowanie w tasach
- Skorygowano nazwy tasków w beat schedule

### ✅ Problem 2: Emaile "sent" ale nie docierają

**Zmieniono:**
- Dodano VERBOSE logging w `MailgunProvider`
- Dodano VERBOSE logging w `EmailQueueProcessor`
- Dodano skrypt testowy `test_mailgun.py`

## Krok po kroku - Jak przetestować

### 1. Restart Celery (WAŻNE!)

```bash
# Zatrzymaj stare procesy
pkill -f celery

# Uruchom na nowo Worker
celery -A celery_app worker -l info > celery_worker.log 2>&1 &

# Uruchom na nowo Beat
celery -A celery_app beat -l info > celery_beat.log 2>&1 &
```

### 2. Sprawdź czy taski są zarejestrowane

```bash
# Aktywuj venv
source .venv/bin/activate

# Sprawdź zarejestrowane taski
celery -A celery_app inspect registered
```

**Powinny być:**
- `app.tasks.email_tasks.monitor_event_changes_task`
- `app.tasks.email_tasks.process_email_queue_task`
- `app.tasks.email_tasks.process_scheduled_campaigns_task`
- `app.tasks.event_tasks.process_event_reminders_task`
- `monitor_member_changes`

### 3. Test Mailgun credentials

```bash
# Aktywuj venv
source .venv/bin/activate

# Uruchom test (zamień na swój email)
python app/utils/test_mailgun.py twoj-email@example.com
```

**Co sprawdzi test:**
- ✅ Czy API key jest poprawny
- ✅ Czy domain jest poprawny
- ✅ Czy API odpowiada
- ✅ Czy email faktycznie się wysyła
- ✅ Czy dostaniesz Message ID z Mailgun

**Możliwe problemy:**

#### Problem: "401 Unauthorized"
**Rozwiązanie:** 
- Sprawdź `MAILGUN_API_KEY` w `.env`
- Klucz powinien być w formacie `key-xxx` lub długi token

#### Problem: "Sandbox - Authorized Recipients"
**Rozwiązanie:**
1. Wejdź do Mailgun Dashboard
2. Przejdź do Sending -> Authorized Recipients
3. Dodaj swój email
LUB
4. Zmień plan na płatny

#### Problem: "404 Not Found"
**Rozwiązanie:**
- Sprawdź `MAILGUN_DOMAIN` w `.env`
- Sprawdź czy używasz właściwego regionu (EU vs US)

### 4. Sprawdź logi Celery (Verbose Mode)

```bash
# Nowe logi będą bardzo szczegółowe

# Worker logs
tail -f celery_worker.log

# Beat logs  
tail -f celery_beat.log

# App logs
tail -f app/logs/app_console.log
```

**Czego szukać w logach:**

#### Dla Celery tasków:
```
🔍 Rozpoczynam monitorowanie zmian w wydarzeniach
📅 Przetwarzam wydarzenie: Tytuł (ID: 123)
✅ Przetworzono 5 wydarzeń
```

#### Dla Mailgun:
```
📤 Mailgun: Próba wysłania do user@example.com
   Temat: Test
   API URL: https://api.mailgun.net/v3/...
   API Key configured: Yes
   Domain: yourdomain.com
🔄 Wysyłam request do Mailgun...
📬 Mailgun response: status_code=200
✅ Email wysłany pomyślnie!
   Message ID: <xxx@yourdomain.com>
```

### 5. Test całego flow

```bash
# 1. Zmień datę wydarzenia w panelu admina

# 2. Sprawdź logi - powinno się pojawić:
tail -f app/logs/app_console.log
# Szukaj: "🔄 Rescheduling przypomnień dla wydarzenia"

# 3. Sprawdź kolejkę w bazie
```

```python
from app import create_app, db
from app.models import EmailQueue

app = create_app()
with app.app_context():
    # Zobacz kolejkę
    pending = EmailQueue.query.filter_by(status='pending').all()
    
    for email in pending:
        print(f"ID: {email.id}")
        print(f"  Do: {email.recipient_email}")
        print(f"  Template: {email.template_name}")
        print(f"  Scheduled: {email.scheduled_at}")
        print(f"  Priority: {email.priority}")
        print()
```

### 6. Wymuś przetworzenie kolejki (opcjonalne)

```python
from app import create_app
from app.tasks.email_tasks import process_email_queue_task

app = create_app()
with app.app_context():
    # Wymuś przetworzenie
    result = process_email_queue_task.apply_async()
    print(f"Task ID: {result.id}")
```

## Debugging checklist

### Jeśli Celery taski się nie uruchamiają:

- [ ] Celery Worker działa (`ps aux | grep celery`)
- [ ] Celery Beat działa
- [ ] Taski są zarejestrowane (`celery -A celery_app inspect registered`)
- [ ] W logach pojawiają się wpisy (nie są puste)
- [ ] Beat schedule ma poprawne nazwy tasków

### Jeśli emaile się nie wysyłają:

- [ ] Test Mailgun przeszedł (`python app/utils/test_mailgun.py`)
- [ ] Mailgun API key jest poprawny
- [ ] Mailgun domain jest poprawny
- [ ] Nie używasz sandbox mode bez authorized recipients
- [ ] W logach widzisz "📤 Mailgun: Próba wysłania..."
- [ ] Status code z Mailgun to 200
- [ ] Dostałeś Message ID
- [ ] Sprawdziłeś Mailgun Dashboard -> Logs

### Jeśli monitor nie wykrywa zmian:

- [ ] Task `monitor_event_changes_task` jest zarejestrowany
- [ ] W beat schedule jest wpis `monitor-event-changes`
- [ ] Task uruchamia się co 15 minut
- [ ] Wydarzenie ma `is_active=True`
- [ ] W logach widzisz "🔍 Rozpoczynam monitorowanie zmian"

## Przydatne komendy

```bash
# Restart Celery
pkill -f celery && celery -A celery_app worker -l info & celery -A celery_app beat -l info &

# Sprawdź co działa
ps aux | grep celery

# Logi real-time
tail -f celery_worker.log celery_beat.log app/logs/app_console.log

# Test Mailgun
python app/utils/test_mailgun.py twoj-email@example.com

# Sprawdź kolejkę
python -c "from app import create_app, db; from app.models import EmailQueue; app = create_app(); app.app_context().push(); print(f'Pending: {EmailQueue.query.filter_by(status=\"pending\").count()}')"

# Debugowanie wydarzenia
python app/utils/debug_event_scheduling.py 123
```

## Kontakt / Support

Jeśli nadal masz problemy:

1. **Zbierz informacje:**
   ```bash
   # Logi
   tail -100 celery_worker.log > debug_worker.log
   tail -100 app/logs/app_console.log > debug_app.log
   
   # Test Mailgun
   python app/utils/test_mailgun.py test@example.com > debug_mailgun.log
   
   # Registered tasks
   celery -A celery_app inspect registered > debug_tasks.log
   ```

2. **Sprawdź .env:**
   ```bash
   grep MAILGUN .env
   grep MAIL_ .env
   ```

3. **Podeślij:**
   - debug_*.log files
   - Opis problemu
   - Co widzisz w Mailgun Dashboard

## Logi które powinieneś zobaczyć po naprawie

### Dobry przykład (wszystko działa):

```
🔍 Rozpoczynam monitorowanie zmian w wydarzeniach
📅 Znaleziono 5 aktywnych wydarzeń z reminders_scheduled=True
📅 Sprawdzam wydarzenie ID: 123
   Emaile w kolejce: 99
   Wszystko OK, daty się zgadzają
✅ Monitorowanie zakończone: sprawdzono 5 wydarzeń, zreschedule'owano 0

📤 PROCESSOR: Rozpoczynam wysyłkę emaila ID: 456
   Do: user@example.com
   Temat: Przypomnienie o wydarzeniu
🔍 Sprawdzam dostępność Mailgun...
   Mailgun available: True
📮 Próba wysyłki przez Mailgun...
📤 Mailgun: Próba wysłania do user@example.com
   API URL: https://api.mailgun.net/v3/...
   API Key configured: Yes
🔄 Wysyłam request do Mailgun...
📬 Mailgun response: status_code=200
✅ Email wysłany pomyślnie!
   Message ID: <xxx@domain.com>
```

### Zły przykład (coś nie działa):

```
❌ Mailgun nie jest dostępny (brak API key lub domain)
❌ SMTP nie jest dostępny
❌ Brak dostępnych providerów!
```

ALBO:

```
(puste logi - taski się nie uruchamiają)
```

## Podsumowanie

Po tej naprawie:
1. ✅ Celery taski będą miały poprawne nazwy i będą się uruchamiać
2. ✅ System będzie monitorować zmiany wydarzeń co 15 minut
3. ✅ Zobaczysz DOKŁADNIE co się dzieje podczas wysyłki emaili
4. ✅ Będziesz mógł łatwo zdiagnozować problemy z Mailgun
5. ✅ Dostaniesz Message ID dla każdego wysłanego emaila
6. ✅ Możesz przetestować Mailgun niezależnie od całej aplikacji

Powodzenia! 🚀

