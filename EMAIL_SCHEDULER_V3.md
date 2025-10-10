# Email Scheduler v3 - Dokumentacja

## Przegląd

Nowy system planowania emaili został przepisany od nowa z jasną hierarchią typów wiadomości i inteligentnym planowaniem przypomnień o wydarzeniach.

## Typy emaili i priorytety

| Typ | Priorytet | Czas wysyłki | Przykłady |
|-----|-----------|--------------|-----------|
| Inne maile systemowe | 0 (najwyższy) | Natychmiast | Reset hasła, powitania, alerty bezpieczeństwa |
| Powiadomienia o wydarzeniach | 1 | 24h/1h/5min przed | Przypomnienia o wydarzeniach |
| Kampanie natychmiastowe | 2 | Natychmiast | Newslettery, ogłoszenia |
| Kampanie planowane | 2 | Według scheduled_at | Zaplanowane przez admina kampanie |

## Główne komponenty

### 1. EmailScheduler (`app/services/email_v2/queue/scheduler.py`)

Główny komponent odpowiedzialny za planowanie emaili.

#### Metody publiczne:

**`schedule_immediate_email(to_email, template_name, context, email_type='system')`**
- Używane dla: maili systemowych i innych natychmiastowych
- Priorytet: 0 (system) lub 2 (inne)
- Przykład:
```python
from app.services.email_v2.queue.scheduler import EmailScheduler

scheduler = EmailScheduler()
success, message = scheduler.schedule_immediate_email(
    to_email='user@example.com',
    template_name='password_reset',
    context={'reset_link': 'https://...'},
    email_type='system'
)
```

**`schedule_campaign(campaign_id)`**
- Używane dla: kampanii emailowych (natychmiastowych i planowanych)
- Priorytet: 2
- Dodaje wszystkie emaile kampanii do kolejki od razu
- Przykład:
```python
scheduler = EmailScheduler()
success, message = scheduler.schedule_campaign(campaign_id=123)
```

**`schedule_event_reminders(event_id)`**
- Używane dla: przypomnień o wydarzeniach
- Priorytet: 1
- Inteligentne wyliczanie które przypomnienia wysłać
- Logika:
  - Jeśli do wydarzenia >= 24h: wysyła 3 przypomnienia (24h, 1h, 5min)
  - Jeśli do wydarzenia >= 1h: wysyła 2 przypomnienia (1h, 5min)
  - Jeśli do wydarzenia >= 5min: wysyła 1 przypomnienie (5min)
  - Jeśli do wydarzenia < 5min: nie wysyła nic
- Przykład:
```python
scheduler = EmailScheduler()
success, message = scheduler.schedule_event_reminders(event_id=456)
```

### 2. EmailQueueProcessor (`app/services/email_v2/queue/processor.py`)

Procesor kolejki emaili z priorytetyzacją.

**Sortowanie kolejki:**
1. Najpierw po priorytecie (0 > 1 > 2)
2. Potem po scheduled_at (najstarsze pierwsze)

**Metoda:**
```python
from app.services.email_v2.queue.processor import EmailQueueProcessor

processor = EmailQueueProcessor()
stats = processor.process_queue(limit=50)
# {'processed': 50, 'success': 48, 'failed': 2}
```

### 3. Taski Celery

**`process_event_reminders_task`** (`app/tasks/event_tasks.py`)
- Uruchamiany: co 5 minut
- Funkcja: Sprawdza aktywne wydarzenia bez zaplanowanych przypomnień i wywołuje `scheduler.schedule_event_reminders()`
- Uproszczony kod - teraz tylko wywołuje scheduler

**`process_scheduled_campaigns_task`** (`app/tasks/email_tasks.py`)
- Uruchamiany: co 1 minutę
- Funkcja: Znajduje kampanie do zaplanowania (draft + immediate lub scheduled + scheduled_at <= now) i wywołuje `scheduler.schedule_campaign()`
- Uproszczony kod - teraz tylko wywołuje scheduler

**`process_email_queue_task`** (`app/tasks/email_tasks.py`)
- Uruchamiany: co 1 minutę
- Funkcja: Przetwarza kolejkę emaili z priorytetyzacją
- Bez zmian

## Migracja z poprzedniego systemu

### Dla maili systemowych:

**Przed:**
```python
email_manager.send_template_email(
    to_email='user@example.com',
    template_name='password_reset',
    context={...},
    priority=1
)
```

**Po:**
```python
email_manager.send_template_email(
    to_email='user@example.com',
    template_name='password_reset',
    context={...},
    email_type='system'  # Zamiast priority
)
```

### Dla wydarzeń:

Bez zmian - używaj dalej `email_manager.send_event_reminders(event_id)`

### Dla kampanii:

Kampanie są automatycznie planowane przez task `process_scheduled_campaigns_task`. 
Wystarczy utworzyć kampanię w bazie z odpowiednim statusem i typem.

## Testowanie

### Testy jednostkowe

```bash
# Aktywuj venv
source .venv/bin/activate

# Uruchom testy
python -m pytest tests/test_email_scheduler.py -v
```

### Testy manualne

```bash
# Aktywuj venv
source .venv/bin/activate

# Uruchom skrypt testowy
python app/utils/test_email_scheduler_manual.py
```

Skrypt testowy:
1. Tworzy wydarzenia testowe (za 48h, 2h, 10min)
2. Tworzy kampanie testowe (natychmiastowa, planowana)
3. Planuje emaile dla wszystkich
4. Wyświetla statystyki kolejki

## Kontrola duplikatów

System używa **dwupoziomowego mechanizmu zapobiegania duplikatom**:

### 1. Dla przypomnień o wydarzeniach (najsilniejsza ochrona)

**a) Tabela `EmailReminder`** (główna ochrona)
- Unikalne ograniczenie na: `(user_id, event_id, reminder_type)`
- Sprawdzane **przed** dodaniem do kolejki
- Dodawane **po** zaplanowaniu emaila
- Używa `user_id` (nie email) - precyzyjniejsze i bezpieczniejsze

**b) Klucz duplikatu w `EmailQueue`**
- Format: `event_reminder_{event_id}_{user_id}_{template_id}_{reminder_type}`
- Zapasowa ochrona na poziomie kolejki

**Przykład:**
```python
# Sprawdź w EmailReminder
existing_reminder = EmailReminder.query.filter_by(
    user_id=participant.id,
    event_id=event_id,
    reminder_type='24h'
).first()

if existing_reminder:
    # Pomijamy - już zaplanowane
    continue

# Dodaj do EmailQueue
success, message, queue_id = scheduler._add_to_queue(...)

# Zapisz w EmailReminder
email_reminder = EmailReminder(
    user_id=participant.id,
    event_id=event_id,
    reminder_type='24h',
    email_queue_id=queue_id
)
db.session.add(email_reminder)
```

### 2. Dla kampanii

**Klucz duplikatu:**
- Format: `campaign_{campaign_id}_{email}`
- Używa email (nie user_id) bo kampanie mogą mieć custom emails
- Zapobiega wysłaniu tej samej kampanii do tego samego odbiorcy

### 3. Dla pozostałych emaili

- Sprawdzanie po: `recipient_email + subject + content_hash`
- Podstawowa ochrona przed przypadkowymi duplikatami

## Przykłady użycia

### 1. Wysłanie emaila o resetie hasła (priorytet 0)

```python
from app.services.email_v2.queue.scheduler import EmailScheduler

scheduler = EmailScheduler()
success, message = scheduler.schedule_immediate_email(
    to_email='jan.kowalski@example.com',
    template_name='password_reset',
    context={
        'user_name': 'Jan',
        'reset_link': 'https://klublepszezycie.pl/reset/abc123',
        'expiry_time': '24 godziny'
    },
    email_type='system'
)
```

### 2. Zaplanowanie przypomnień o wydarzeniu (priorytet 1)

```python
from app.services.email_v2.queue.scheduler import EmailScheduler

scheduler = EmailScheduler()
success, message = scheduler.schedule_event_reminders(event_id=123)

if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")
```

### 3. Wysłanie kampanii natychmiastowej (priorytet 2)

```python
# 1. Utwórz kampanię w bazie
campaign = EmailCampaign(
    name='Newsletter październik 2025',
    subject='Nowości w klubie',
    html_content='<p>...</p>',
    recipient_type='groups',
    recipient_groups='[1, 2, 3]',  # ID grup
    status='draft',
    send_type='immediate'
)
db.session.add(campaign)
db.session.commit()

# 2. Zaplanuj kampanię
scheduler = EmailScheduler()
success, message = scheduler.schedule_campaign(campaign.id)
```

### 4. Zaplanowanie kampanii na przyszłość (priorytet 2)

```python
from datetime import datetime, timedelta

# 1. Utwórz kampanię w bazie
scheduled_time = datetime.now() + timedelta(days=7)

campaign = EmailCampaign(
    name='Newsletter za tydzień',
    subject='Nowości',
    html_content='<p>...</p>',
    recipient_type='groups',
    recipient_groups='[1]',
    status='draft',
    send_type='scheduled',
    scheduled_at=scheduled_time
)
db.session.add(campaign)
db.session.commit()

# 2. Kampania zostanie automatycznie zaplanowana przez task Celery
# Lub możesz zaplanować ją manualnie:
scheduler = EmailScheduler()
success, message = scheduler.schedule_campaign(campaign.id)
```

## Monitoring

### Sprawdzenie kolejki

```python
from app.models import EmailQueue

# Emaile oczekujące według priorytetu
pending = EmailQueue.query.filter_by(status='pending').order_by(
    EmailQueue.priority.asc(),
    EmailQueue.scheduled_at.asc()
).all()

for email in pending:
    print(f"Priorytet: {email.priority} | Template: {email.template_name} | To: {email.recipient_email}")
```

### Statystyki kolejki

```python
from app.services.email_v2.manager import EmailManager

manager = EmailManager()
stats = manager.get_stats()
print(stats)
# {'total': 150, 'pending': 100, 'sent': 45, 'failed': 5, 'processing': 0}
```

## Konfiguracja Celery

Upewnij się, że taski są poprawnie skonfigurowane w `celery_app.py`:

```python
celery.conf.beat_schedule = {
    # Monitorowanie zmian w wydarzeniach - co 15 minut
    'monitor-event-changes': {
        'task': 'app.tasks.email_tasks.monitor_event_changes_task',
        'schedule': 900.0,  # Co 15 minut
        'options': {'queue': 'event_queue'},
    },
    
    # Planowanie przypomnień o wydarzeniach - co 5 minut
    'process-event-reminders': {
        'task': 'app.tasks.event_tasks.process_event_reminders_task',
        'schedule': 300.0,  # Co 5 minut
        'options': {'queue': 'event_queue'},
    },
    
    # Planowanie kampanii - co 1 minutę
    'process-scheduled-campaigns': {
        'task': 'app.tasks.email_tasks.process_scheduled_campaigns_task',
        'schedule': 60.0,  # Co 1 minutę
    },
    
    # Przetwarzanie kolejki - co 1 minutę
    'process-email-queue': {
        'task': 'app.tasks.email_tasks.process_email_queue_task',
        'schedule': 60.0,  # Co 1 minutę
    },
}
```

### Task: `monitor_event_changes_task`

**Uruchamiany:** Co 15 minut

**Funkcja:** Automatyczne wykrywanie i naprawianie niespójności

**Co robi:**
1. Sprawdza wszystkie aktywne wydarzenia z `reminders_scheduled=True`
2. Dla każdego wydarzenia sprawdza czy emaile w kolejce mają poprawne daty
3. Jeśli wykryje niespójność (różnica > 5 minut), automatycznie reschedule'uje
4. Jeśli wydarzenie ma flagę ale brak emaili w kolejce, resetuje flagę

**Przykład wykrytej niespójności:**
```
⚠️ Niespójność dla wydarzenia 123: 
   oczekiwano 2025-10-15 12:00:00
   jest       2025-10-10 12:00:00
   różnica:   432000 sekund (5 dni)
🔄 Reschedule przypomnień dla wydarzenia 123
✅ Zreschedule'owano: Zaplanowano 99 przypomnień
```

## Reschedule przypomnień (zmiana daty wydarzenia)

### Problem
Gdy admin zmienia datę wydarzenia, stare przypomnienia pozostają w kolejce z nieaktualnymi datami.

### Rozwiązanie

System **automatycznie** reschedule'uje przypomnienia na 3 sposoby:

1. **Natychmiast** - gdy admin zmienia datę w panelu admina (API)
2. **Okresowo** - task `monitor_event_changes_task` co 15 minut wykrywa niespójności
3. **Manualnie** - przez API endpoint lub skrypt CLI

#### Metoda 1: Automatyczny reschedule (API)

Gdy edytujesz wydarzenie w panelu admina, system automatycznie wykrywa zmianę daty i reschedule'uje przypomnienia.

**Endpoint:** `PUT /api/events/schedules/<event_id>`

Odpowiedź będzie zawierać:
```json
{
  "success": true,
  "message": "Harmonogram został zaktualizowany. Rescheduling zakończony: Zaplanowano 99 przypomnień dla 33 uczestników (usunięto 99 starych emaili)",
  "event_date_changed": true,
  "reminders_rescheduled": true
}
```

#### Metoda 2: Manualny reschedule (API)

Jeśli chcesz ręcznie zreschedule'ować przypomnienia:

**Endpoint:** `POST /api/events/schedules/<event_id>/reschedule-reminders`

```javascript
fetch('/api/events/schedules/123/reschedule-reminders', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

#### Metoda 3: Skrypt CLI

Użyj skryptu pomocniczego z terminala:

```bash
# Aktywuj venv
source .venv/bin/activate

# Lista wszystkich wydarzeń
python app/utils/reschedule_event.py list

# Reschedule konkretnego wydarzenia
python app/utils/reschedule_event.py 123
```

#### Metoda 4: Kod Python

```python
from app.services.email_v2.queue.scheduler import EmailScheduler

scheduler = EmailScheduler()
success, message = scheduler.reschedule_event_reminders(event_id=123)

if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")
```

### Co robi reschedule?

1. **Usuwa stare emaile** z `EmailQueue` (status='pending')
2. **Usuwa stare wpisy** z `EmailReminder`
3. **Resetuje flagę** `reminders_scheduled = False`
4. **Planuje nowe przypomnienia** na podstawie nowej daty

## Rozwiązywanie problemów

### Przypomnienia o wydarzeniu nie są wysyłane

1. Sprawdź czy wydarzenie ma `reminders_scheduled = False`
2. Sprawdź czy jest czas do wydarzenia (>= 5 min)
3. Sprawdź czy są uczestnicy (członkowie klubu + grupa wydarzenia)
4. Sprawdź czy istnieją szablony: `event_reminder_24h`, `event_reminder_1h`, `event_reminder_5min`

### Zmieniłem datę wydarzenia, ale nie widzę nowych emaili

1. System powinien automatycznie zreschedule'ować (sprawdź logi)
2. Jeśli nie, użyj manualnego reschedulingu:
   ```bash
   python app/utils/reschedule_event.py 123
   ```
3. Lub przez API:
   ```bash
   curl -X POST http://localhost:5000/api/events/schedules/123/reschedule-reminders
   ```

### Kampania nie jest planowana

1. Sprawdź status kampanii (powinien być 'draft')
2. Sprawdź czy są odbiorcy
3. Dla kampanii planowanych: sprawdź `scheduled_at` (nie może być w przeszłości)

### Emaile nie są wysyłane

1. Sprawdź czy Celery działa: `celery -A celery_app worker -l info`
2. Sprawdź czy Celery Beat działa: `celery -A celery_app beat -l info`
3. Sprawdź logi: `app/logs/app_console.log`
4. Sprawdź kolejkę emaili w bazie: `SELECT * FROM email_queue WHERE status='pending'`

## Najlepsze praktyki

### 1. Używaj ID zamiast nazw

**✅ Dobrze:**
```python
# Szablony cache'owane po ID
templates_cache = {}
for reminder_type in ['24h', '1h', '5min']:
    template = EmailTemplate.query.filter_by(name=f'event_reminder_{reminder_type}').first()
    templates_cache[reminder_type] = template

# Używaj user_id w kluczach
duplicate_key = f"event_{event_id}_{user.id}_{template.id}"
```

**❌ Źle:**
```python
# Wielokrotne query po name
template = EmailTemplate.query.filter_by(name='event_reminder_24h').first()
# ...
template = EmailTemplate.query.filter_by(name='event_reminder_1h').first()

# Email w kluczach (mniej precyzyjne)
duplicate_key = f"event_{event_id}_{user.email}"
```

**Dlaczego ID są lepsze:**
- ✅ Unikalne i niezmienne
- ✅ Szybsze wyszukiwanie (indeks na primary key)
- ✅ Bezpieczniejsze (nie zależne od zmian nazw)
- ✅ Lepsze dla relacji w bazie danych

### 2. Wykorzystuj model EmailReminder

Model `EmailReminder` zapewnia:
- **Unikalne ograniczenie** na (user_id, event_id, reminder_type)
- **Historię** wysłanych przypomnień
- **Linkowanie** z EmailQueue przez email_queue_id
- **Automatyczną ochronę** przed duplikatami na poziomie bazy

### 3. Cache szablonów

Dla wydajności, ładuj szablony raz i cache'uj:
```python
# Cache wszystkich potrzebnych szablonów
templates_cache = {}
for reminder_type in reminders_to_send:
    template = EmailTemplate.query.filter_by(
        name=f'event_reminder_{reminder_type}'
    ).first()
    if template:
        templates_cache[reminder_type] = template

# Używaj z cache
for participant in participants:
    for reminder_type in reminders_to_send:
        template = templates_cache.get(reminder_type)
        if not template:
            continue
        # ...
```

## Changelog

### v3.0.0 (Październik 2025)

**Nowe funkcje:**
- ✅ Przepisany EmailScheduler z czystą architekturą
- ✅ Hierarchia priorytetów (0 > 1 > 2)
- ✅ Inteligentne planowanie przypomnień o wydarzeniach
- ✅ Wszystkie emaile w EmailQueue od razu (nie ma opóźnień)
- ✅ **Dwupoziomowa kontrola duplikatów** (EmailReminder + EmailQueue)
- ✅ **Używanie user_id zamiast email** w kluczach duplikatów
- ✅ **Cache szablonów po ID** dla wydajności
- ✅ **3-poziomowy automatyczny reschedule:**
  - Natychmiast przez API gdy admin edytuje wydarzenie
  - Okresowo (co 15 min) przez task monitorujący
  - Manualnie przez API endpoint lub skrypt CLI
- ✅ **Monitoring niespójności** w kolejce emaili
- ✅ Uproszczone taski Celery

**Zmiany:**
- 🔄 `EmailScheduler` - całkowicie przepisany
- 🔄 `EmailScheduler.schedule_event_reminders()` - dodany parametr `force`
- 🔄 `EmailScheduler.reschedule_event_reminders()` - nowa metoda
- 🔄 `EmailQueueProcessor` - dodane sortowanie po priorytetach
- 🔄 `EmailManager.send_template_email()` - dodany parametr `email_type`
- 🔄 `_add_to_queue()` - zwraca teraz (success, message, queue_id)
- 🔄 `PUT /api/events/schedules/<id>` - automatyczny reschedule gdy zmienia się data
- 🔄 Taski Celery - uproszczone, teraz tylko wywołują scheduler

**Nowe Celery taski:**
- ✅ `monitor_event_changes_task` - monitoruje zmiany i niespójności (co 15 min)
- 🔄 `update_event_notifications_task` - przepisany, używa reschedule

**Nowe API endpointy:**
- ✅ `POST /api/events/schedules/<id>/reschedule-reminders` - manualny reschedule

**Nowe skrypty:**
- ✅ `app/utils/reschedule_event.py` - CLI tool do reschedulingu

**Usunięte:**
- ❌ Stara logika planowania z wielu miejsc skonsolidowana w jednym schedulerze
- ❌ Wielokrotne query po template name - zastąpione cache'owaniem

