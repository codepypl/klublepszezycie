# System Archiwizacji Wydarzeń

## Przegląd

System automatycznie archiwizuje zakończone wydarzenia i czyści powiązane z nimi grupy użytkowników.

## Funkcjonalności

### 1. Automatyczna Archiwizacja Wydarzeń

**Kiedy wydarzenie jest uznawane za zakończone:**
- Jeśli ma `end_date`: gdy obecny czas przekroczy `end_date`
- Jeśli nie ma `end_date`: gdy obecny czas przekroczy `event_date`

**Co się dzieje podczas archiwizacji:**
1. Wydarzenie jest oznaczone jako `is_archived = True`, `is_active = False` i `is_published = False`
2. Wszyscy członkowie są usuwani z grup wydarzenia
3. Grupy wydarzenia są usuwane z systemu
4. Historia uczestnictwa pozostaje zachowana

**Wpływ na widoczność wydarzeń:**
- Wydarzenia archiwalne nie są wyświetlane na stronie głównej
- Wydarzenia archiwalne nie są publikowane (nie można się na nie zapisać)
- Wydarzenia archiwalne można przeglądać w panelu administracyjnym z odpowiednimi filtrami

### 2. Czyszczenie Grup

**Grupy wydarzeń (`event_based`):**
- Automatycznie usuwane po archiwizacji wydarzenia
- Wszyscy członkowie są usuwani przed usunięciem grupy

**Grupy sieroce:**
- Grupy bez powiązanego wydarzenia są automatycznie usuwane
- Grupy z nieprawidłowymi kryteriami są usuwane

## Sposoby Uruchomienia

### 1. Skrypt Ręczny
```bash
cd /path/to/project
source .venv/bin/activate
python archive_events.py
```

### 2. API Endpoint (Admin Only)
```http
POST /api/events/archive-ended
Authorization: Bearer <admin_token>
```

### 3. Automatyzacja (Cron)
Dodaj do crontab:
```bash
# Codziennie o 2:00 AM
0 2 * * * cd /path/to/project && source .venv/bin/activate && python archive_events.py
```

## Metody Modelu EventSchedule

### `is_ended()`
Sprawdza czy wydarzenie się zakończyło:
```python
if event.is_ended():
    # Wydarzenie się zakończyło
```

### `archive()`
Archiwizuje wydarzenie i czyści grupy:
```python
success, message = event.archive()
if success:
    print("Wydarzenie zarchiwizowane")
else:
    print(f"Błąd: {message}")
```

## Metody GroupManager

### `cleanup_event_groups(event_id)`
Usuwa wszystkich członków z grup wydarzenia:
```python
success, message = group_manager.cleanup_event_groups(event_id)
```

### `delete_event_groups(event_id)`
Usuwa grupy wydarzenia z systemu:
```python
success, message = group_manager.delete_event_groups(event_id)
```

### `cleanup_orphaned_groups()`
Usuwa nieużywane grupy wydarzeń:
```python
success, message = group_manager.cleanup_orphaned_groups()
```

## Logi i Monitorowanie

System loguje wszystkie operacje:
- ✅ Sukces: `Zarchiwizowano wydarzenie: {title}`
- 🧹 Czyszczenie: `Wyczyściono grupę: {name}`
- 🗑️ Usuwanie: `Usunięto grupę: {name}`
- ❌ Błędy: `Błąd archiwizacji: {error}`

## Bezpieczeństwo

- Archiwizacja zachowuje historię uczestnictwa (`UserHistory`)
- Usuwa tylko grupy wydarzeń, nie wpływa na inne grupy
- Operacje są transakcyjne - w przypadku błędu zmiany są cofane
- Wymaga uprawnień administratora dla API endpoint

## Przykład Użycia

```python
from app.services.email_automation import EmailAutomation
from app.services.group_manager import GroupManager

# Archiwizacja wydarzeń
email_automation = EmailAutomation()
success, message = email_automation.archive_ended_events()

# Czyszczenie grup
group_manager = GroupManager()
success, message = group_manager.cleanup_orphaned_groups()
```

## Status Wydarzeń

- **Aktywne** (`is_active=True, is_archived=False`): Widoczne na stronie
- **Zarchiwizowane** (`is_active=False, is_archived=True`): Ukryte, historia zachowana
- **Zakończone**: Automatycznie archiwizowane
