# Migracje bazy danych

## Opis
Ten katalog zawiera migracje bazy danych dla aplikacji Lepsze Życie Club.

## Pliki migracji

### 20250929_110710_add_reminders_scheduled_to_event_schedule.py
- **Data**: 2025-09-29 11:07:10
- **Opis**: Dodaje kolumnę `reminders_scheduled` do tabeli `event_schedule`
- **Cel**: Zabezpieczenie przed duplikatami przypomnień o wydarzeniach
- **Typ**: BOOLEAN, domyślnie FALSE

## Użycie

### Uruchomienie migracji
```bash
# Uruchom wszystkie migracje
python -c "from app import create_app; from app import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Cofnięcie migracji
```bash
# Cofnij ostatnią migrację (jeśli potrzebne)
# Uwaga: Ta migracja nie może być cofnięta automatycznie
```

## Uwagi
- Migracja została już wykonana bezpośrednio na bazie danych
- Kolumna `reminders_scheduled` jest używana przez system zabezpieczeń przed duplikatami
- Wszystkie istniejące rekordy mają wartość `FALSE`
