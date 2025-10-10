# Optymalizacja Bazy Danych - Dokumentacja

## Przegląd zmian

Migracja `871d187c04c0` usuwa legacy kolumny, dodaje SEO i optymalizuje strukturę bazy danych.

### Usunięte elementy:

1. **User.role** - duplikat `account_type`
2. **User.event_id** - zastąpione przez `EventRegistration`  
3. **User.group_id** - zastąpione przez `UserGroupMember`
4. **Tabela `default_email_templates`** - redundancja (używamy `EmailTemplate` z `is_default=True`)

### Dodane elementy:

1. **EventSchedule.slug** - SEO-friendly URLs dla wydarzeń (`/events/warsztaty-ai-2025`)
2. **PasswordResetToken.token = UUID** - zamiast długiego stringa (36 znaków zamiast 43)
3. **Indeks na `EmailQueue.campaign_id`** - przyspiesza query kampanii
4. **Indeks na `EmailLog.campaign_id`** - przyspiesza filtrowanie logów
5. **Indeks na `Call.campaign_id`** - przyspiesza statystyki CRM
6. **Indeks na `EventSchedule.slug`** - szybkie query po slug

## Migracja danych

### Przed uruchomieniem migracji

System automatycznie zmigruje legacy dane:

**User.event_id → EventRegistration:**
```sql
-- 2 userów z event_id zostanie zmigrowanych
INSERT INTO event_registrations (user_id, event_id, ...)
SELECT id, event_id, ...
FROM users
WHERE event_id IS NOT NULL
```

**User.group_id → UserGroupMember:**
```sql
-- 1 user z group_id zostanie zmigrowany
INSERT INTO user_group_members (group_id, user_id, ...)
SELECT group_id, id, ...
FROM users  
WHERE group_id IS NOT NULL
```

**User.role → User.account_type:**
```sql
-- 2 userów z inconsistency zostanie zsynchronizowanych
UPDATE users
SET role = account_type
WHERE role != account_type
```

### Uruchomienie migracji

```bash
# 1. Backup bazy danych (WAŻNE!)
pg_dump -U shadi betterlife > backup_before_optimization_$(date +%Y%m%d).sql

# 2. Aktywuj venv
cd /Volumes/Dane/Projekty/devs/klublepszezycie
source .venv/bin/activate

# 3. Uruchom migrację
cd app/migrations
alembic upgrade head

# 4. Sprawdź czy migracja przebiegła pomyślnie
alembic current
```

### Weryfikacja po migracji

```bash
# Sprawdź czy legacy kolumny zostały usunięte
python -c "
from app import create_app
from app.models import User
import sqlalchemy as sa

app = create_app()
with app.app_context():
    inspector = sa.inspect(User.metadata.bind)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    print('Kolumny w tabeli users:')
    for col in columns:
        print(f'  - {col}')
    
    if 'role' in columns:
        print('❌ BŁĄD: kolumna role nadal istnieje!')
    else:
        print('✅ Kolumna role usunięta')
    
    if 'event_id' in columns:
        print('❌ BŁĄD: kolumna event_id nadal istnieje!')
    else:
        print('✅ Kolumna event_id usunięta')
    
    if 'group_id' in columns:
        print('❌ BŁĄD: kolumna group_id nadal istnieje!')
    else:
        print('✅ Kolumna group_id usunięta')
"

# Sprawdź czy indeksy zostały dodane
python -c "
from app import create_app
from app.models import EmailQueue
import sqlalchemy as sa

app = create_app()
with app.app_context():
    inspector = sa.inspect(EmailQueue.metadata.bind)
    indexes = inspector.get_indexes('email_queue')
    
    print('Indeksy w email_queue:')
    for idx in indexes:
        print(f'  - {idx[\"name\"]}')
"
```

## Nowe funkcje

### 1. SEO-friendly URLs dla wydarzeń

**EventSchedule.slug**:
```python
# PRZED: /admin/events/123
# PO: /admin/events/warsztaty-ai-2025

event = EventSchedule(title="Warsztaty AI 2025")
event.generate_slug()  # Automatycznie tworzy slug
# event.slug = "warsztaty-ai-2025"

# Query po slug
event = EventSchedule.query.filter_by(slug='warsztaty-ai-2025').first()
```

**Zalety**:
- ✅ SEO-friendly (Google lepiej indeksuje)
- ✅ Czytelne URL
- ✅ Ukrywa liczbę wydarzeń
- ✅ Unikalny (indexed)

### 2. UUID dla Password Reset

**PasswordResetToken.token**:
```python
# PRZED: token = secrets.token_urlsafe(32) 
# "xK3mP9-fT2jR8vQ1wN5hL7zY4bC6dF0aG2eH8iJ3kM9n"  # 43 znaki

# PO: token = uuid.uuid4()
# "550e8400-e29b-41d4-a716-446655440000"  # 36 znaków, standardowy format

# Użycie
token = PasswordResetToken.generate_token()  # UUID v4
```

**Zalety**:
- ✅ Krótszetoken (36 vs 43 znaki)
- ✅ Standardowy format (UUID)
- ✅ Indexed dla szybkiego lookup
- ✅ Bezpieczny (128 bitów entropii)

### 3. Unsubscribe tokens (bez zmian)

**Format HMAC - zostaje!**
```python
# Format: user_id.timestamp.action.signature
# "264.1762665008.unsubscribe.99061aa92cbfad80"

# Zalety HMAC:
# ✅ Stateless (nie zajmuje miejsca w bazie)
# ✅ Bezpieczny (HMAC signed, nie da się podrobić)
# ✅ Krótki (~43 znaki)
# ✅ Zawiera wszystkie dane w tokenie
```

## Zmiany w kodzie

### 1. Model User

**PRZED:**
```python
class User(db.Model):
    role = db.Column(db.String(20))  # ❌ Usunięte
    account_type = db.Column(db.String(30))
    event_id = db.Column(db.Integer)  # ❌ Usunięte
    group_id = db.Column(db.Integer)  # ❌ Usunięte
```

**PO:**
```python
class User(db.Model):
    account_type = db.Column(db.String(30))  # ✅ Jedyne pole dla ról
```

### 2. Model EmailTemplate

**PRZED:**
```python
EmailTemplate - szablony tworzone przez admina
DefaultEmailTemplate - szablony z fixtures  # ❌ Usunięte
```

**PO:**
```python
EmailTemplate - wszystkie szablony
  is_default=True  - szablony systemowe z fixtures
  is_default=False - szablony tworzone przez admina
```

### 3. API Responses

API nadal zwraca `role` dla backward compatibility:

```javascript
// Response
{
  "role": "admin",  // = account_type (dla kompatybilności)
  "account_type": "admin"  
}
```

### 4. Fixture Loader

**PRZED:**
```python
DefaultEmailTemplate.query.filter_by(name='welcome')...
```

**PO:**
```python
EmailTemplate.query.filter_by(name='welcome', is_default=True)...
```

## Korzyści

### Wydajność:
- ✅ **4 nowe indeksy** - EmailQueue, EmailLog, Call, EventSchedule.slug
- ✅ **Mniej JOIN** - brak zbędnych tabel
- ✅ **Szybsze query** - indexed slug lookups

### SEO & UX:
- ✅ **SEO-friendly URLs** - `/events/warsztaty-ai` zamiast `/events/123`
- ✅ **Czytelne linki** - lepsze dla użytkowników
- ✅ **Ukrywa metryki** - nie widać liczby wydarzeń

### Przestrzeń:
- ✅ **3 kolumny usunięte** z `users`
- ✅ **1 tabela usunięta** (`default_email_templates`)
- ✅ **~11 duplikatów** mniej (szablony)
- ✅ **Krótsze tokeny** - UUID (36 znaków) vs urlsafe (43 znaki)

### Utrzymanie:
- ✅ **Brak redundancji** - jedna prawda, jedno miejsce
- ✅ **Prostszy kod** - nie trzeba synchronizować role/account_type
- ✅ **Jasna struktura** - EventRegistration dla wydarzeń, UserGroupMember dla grup
- ✅ **Standardy** - UUID dla tokenów (industry standard)

## Rollback (jeśli potrzeba)

```bash
# Cofnij migrację
cd app/migrations
alembic downgrade -1

# Przywróci:
# - User.role, User.event_id, User.group_id
# - Tabelę default_email_templates
# - Usunie indeksy
```

## Wpływ na istniejący kod

### ✅ Bez zmian (kompatybilność wsteczna):

- `user.is_admin_role()` - używa account_type ✅
- `user.is_ankieter_role()` - używa account_type ✅
- `user.is_user_role()` - zaktualizowane na account_type ✅
- API zwraca `role` = `account_type` ✅

### ⚠️ Może wymagać aktualizacji:

**Jeśli gdzieś używasz:**
```python
user.role  # ❌ Nie istnieje - użyj user.account_type
user.event_id  # ❌ Nie istnieje - użyj EventRegistration
user.group_id  # ❌ Nie istnieje - użyj UserGroupMember
```

**Poprawka:**
```python
user.account_type  # ✅ Zamiast user.role
EventRegistration.is_user_registered(user.id, event.id)  # ✅ Zamiast user.event_id
UserGroupMember.query.filter_by(user_id=user.id)  # ✅ Zamiast user.group_id
```

## Testowanie

### Test 1: Sprawdź role użytkowników

```python
from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    admins = User.query.filter_by(account_type='admin').all()
    ankieters = User.query.filter_by(account_type='ankieter').all()
    users = User.query.filter_by(account_type='user').all()
    
    print(f'Admins: {len(admins)}')
    print(f'Ankieters: {len(ankieters)}')
    print(f'Users: {len(users)}')
```

### Test 2: Sprawdź event registrations

```python
from app import create_app
from app.models import EventRegistration

app = create_app()
with app.app_context():
    registrations = EventRegistration.query.all()
    print(f'Event Registrations: {len(registrations)}')
    
    # Sprawdź zmigrowane dane
    legacy_registrations = EventRegistration.query.filter_by(registration_source='legacy_migration').all()
    print(f'Legacy migrated: {len(legacy_registrations)}')
```

### Test 3: Sprawdź indeksy

```python
import sqlalchemy as sa
from app import create_app

app = create_app()
with app.app_context():
    inspector = sa.inspect(app.extensions['sqlalchemy'].db.engine)
    
    # Email Queue indexes
    indexes = inspector.get_indexes('email_queue')
    campaign_idx = [idx for idx in indexes if 'campaign_id' in idx['name']]
    
    if campaign_idx:
        print('✅ Indeks campaign_id w email_queue istnieje')
    else:
        print('❌ Brak indeksu campaign_id')
```

## Podsumowanie

**Przed:** 32 tabele, 3 zbędne kolumny, brak indeksów na campaign_id
**Po:** 31 tabel (-1), czysta struktura, 3 nowe indeksy

**Status:** Gotowe do uruchomienia migracji!

## Następne kroki

1. **Backup bazy!**
2. Uruchom `alembic upgrade head`
3. Uruchom testy weryfikacyjne
4. Zrestartuj aplikację

Gotowe! 🚀

