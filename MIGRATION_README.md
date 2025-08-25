# Instrukcja migracji bazy danych

## Problem
Błąd: `column event_schedule.hero_background does not exist`

## Rozwiązanie
Należy dodać brakujące kolumny do tabeli `event_schedule`:
- `hero_background` - ścieżka do pliku tła (zdjęcie/wideo)
- `hero_background_type` - typ tła ('image' lub 'video')

## Opcje wykonania migracji

### Opcja 1: Skrypt Python (ZALECANE)
```bash
# Uruchom migrację
python migrate_events.py

# W przypadku problemów - cofnij migrację
python migrate_events.py --rollback
```

### Opcja 2: Skrypt SQL
```bash
# Wykonaj skrypt SQL w swojej bazie danych
psql -d nazwa_bazy_danych -f migrate_events.sql

# Lub w pgAdmin - skopiuj i wklej zawartość pliku migrate_events.sql
```

### Opcja 3: Ręczne wykonanie SQL
```sql
-- Dodaj kolumnę hero_background
ALTER TABLE event_schedule ADD COLUMN hero_background VARCHAR(500);

-- Dodaj kolumnę hero_background_type z domyślną wartością
ALTER TABLE event_schedule ADD COLUMN hero_background_type VARCHAR(20) DEFAULT 'image';
```

## Sprawdzenie migracji
Po wykonaniu migracji sprawdź czy kolumny zostały dodane:

```sql
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'event_schedule'
ORDER BY ordinal_position;
```

## Struktura po migracji
Tabela `event_schedule` powinna zawierać następujące kolumny:
- `id` (INTEGER, PRIMARY KEY)
- `title` (VARCHAR(200))
- `event_type` (VARCHAR(50))
- `event_date` (DATETIME)
- `end_date` (DATETIME)
- `description` (TEXT)
- `meeting_link` (VARCHAR(500))
- `location` (VARCHAR(200))
- `is_active` (BOOLEAN)
- `is_published` (BOOLEAN)
- `hero_background` (VARCHAR(500)) ← NOWA KOLUMNA
- `hero_background_type` (VARCHAR(20)) ← NOWA KOLUMNA
- `created_at` (DATETIME)
- `updated_at` (DATETIME)

## Uwagi
- Migracja jest bezpieczna - sprawdza czy kolumny już istnieją
- Nie usuwa żadnych danych
- Można cofnąć używając `--rollback`
- Po migracji aplikacja powinna działać bez błędów

## W przypadku problemów
1. Sprawdź czy masz uprawnienia do modyfikacji tabeli
2. Upewnij się, że baza danych jest dostępna
3. Sprawdź logi błędów
4. W razie potrzeby skontaktuj się z administratorem bazy danych
