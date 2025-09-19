# 🔧 Instrukcje Naprawy Migracji na Serwerze Produkcyjnym

## 🚨 Problem
Migracja `af25e20522fc` próbuje dodać kolumny do tabeli `user_history`, które już istnieją na serwerze produkcyjnym, powodując błąd:
```
psycopg2.errors.DuplicateColumn: column "registration_type" of relation "user_history" already exists
```

## 🔍 Diagnoza
Na serwerze produkcyjnym struktura tabeli `user_history` różni się od lokalnej. Kolumny z migracji już istnieją, ale migracja nie została oznaczona jako zastosowana.

## 🛠️ Rozwiązanie

### Krok 1: Sprawdzenie struktury tabeli
```bash
# Na serwerze produkcyjnym
cd /apps/klublepszezycie
source .venv/bin/activate
python check_table_structure.py
```

### Krok 2: Naprawa migracji
```bash
# Na serwerze produkcyjnym
python fix_migration.py
```

### Krok 3: Kontynuacja migracji
```bash
# Na serwerze produkcyjnym
flask db upgrade
```

## 📋 Co robi skrypt naprawczy

1. **Sprawdza istniejące kolumny** w tabeli `user_history`
2. **Identyfikuje brakujące kolumny** z migracji
3. **Dodaje brakujące kolumny** ręcznie (jeśli są)
4. **Sprawdza i dodaje constraint'y** (unique constraint, indeksy)
5. **Oznacza migrację jako zastosowaną** w tabeli `alembic_version`
6. **Pozwala na kontynuację** normalnego procesu migracji

## ⚠️ Uwagi Bezpieczeństwa

- **Backup bazy danych** przed uruchomieniem skryptów
- **Test na kopii** jeśli to możliwe
- **Monitorowanie logów** podczas naprawy
- **Sprawdzenie po naprawie** czy wszystko działa poprawnie

## 🔄 Alternatywne Rozwiązanie

Jeśli skrypty nie działają, można ręcznie:

1. **Sprawdzić obecną wersję migracji:**
   ```sql
   SELECT version_num FROM alembic_version;
   ```

2. **Oznaczyć migrację jako zastosowaną:**
   ```sql
   UPDATE alembic_version SET version_num = 'af25e20522fc';
   ```

3. **Kontynuować migrację:**
   ```bash
   flask db upgrade
   ```

## 📞 Wsparcie

W przypadku problemów:
1. Sprawdź logi aplikacji
2. Sprawdź strukturę tabeli `user_history`
3. Sprawdź tabelę `alembic_version`
4. Skontaktuj się z deweloperem
